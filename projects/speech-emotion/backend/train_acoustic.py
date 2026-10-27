"""
HuBERT 情感分类器训练脚本
=========================
用 CASIA 中文情感语音数据集微调 HuBERT 分类头
训练完成后自动更新声学模型权重

用法：python train_acoustic.py
"""

import os
import sys
import time
import pickle
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from tqdm import tqdm

# ============ 配置 ============
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "CASIA_clean"
MODEL_SAVE_PATH = Path(__file__).resolve().parent / "models" / "acoustic_emotion.pt"
BATCH_SIZE = 16
LEARNING_RATE = 1e-3
EPOCHS = 30
DEVICE = torch.device("cpu")

EMOTIONS = ["开心", "悲伤", "愤怒", "中性", "惊讶", "恐惧"]


# ============ 数据集 ============
class CASIADataset(Dataset):
    """CASIA 情感语音数据集加载器"""

    def __init__(self, file_paths, labels):
        self.file_paths = file_paths
        self.labels = labels
        self.feature_extractor = None  # 延迟加载

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        import librosa

        # 加载音频
        waveform, sr = librosa.load(self.file_paths[idx], sr=16000, mono=True)
        # 截断/填充到 3 秒
        target_len = 48000  # 16000 * 3
        if len(waveform) > target_len:
            waveform = waveform[:target_len]
        else:
            waveform = np.pad(waveform, (0, target_len - len(waveform)))

        return torch.FloatTensor(waveform), torch.tensor(self.labels[idx])


# ============ 分类器（与 acoustic.py 中的一致）============
class EmotionClassifier(nn.Module):
    """情感分类头"""

    def __init__(self, input_dim=768, hidden_dim=256, num_classes=6):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x):
        return self.net(x)


# ============ 特征提取 ============
def extract_features(model, processor, dataloader, desc="Extracting"):
    """用 HuBERT 批量提取特征"""
    model.eval()
    features_list = []
    labels_list = []

    with torch.no_grad():
        for waveforms, labels in tqdm(dataloader, desc=desc):
            inputs = processor(
                waveforms.squeeze(1).numpy(),
                sampling_rate=16000,
                return_tensors="pt",
                padding=True,
            )
            input_values = inputs["input_values"].to(DEVICE)
            outputs = model(input_values)
            # 时间维度平均池化 → [B, 768]
            pooled = outputs.last_hidden_state.mean(dim=1)
            features_list.append(pooled.cpu())
            labels_list.append(labels)

    return torch.cat(features_list), torch.cat(labels_list)


# ============ 训练 ============
def train_classifier(train_loader, test_loader, input_dim=768):
    """训练分类头"""
    model = EmotionClassifier(input_dim=input_dim).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", patience=5, factor=0.5
    )

    best_acc = 0
    best_state = None

    for epoch in range(1, EPOCHS + 1):
        # 训练
        model.train()
        train_loss = 0
        correct = 0
        total = 0
        for features, labels in tqdm(train_loader, desc=f"Epoch {epoch}/{EPOCHS}"):
            features, labels = features.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

        train_acc = 100.0 * correct / total
        avg_loss = train_loss / len(train_loader)

        # 验证
        model.eval()
        test_correct = 0
        test_total = 0
        with torch.no_grad():
            for features, labels in test_loader:
                features, labels = features.to(DEVICE), labels.to(DEVICE)
                outputs = model(features)
                _, predicted = outputs.max(1)
                test_total += labels.size(0)
                test_correct += predicted.eq(labels).sum().item()
        test_acc = 100.0 * test_correct / test_total

        scheduler.step(1 - test_acc / 100)

        print(f"  Loss={avg_loss:.4f}  Train={train_acc:.1f}%  Test={test_acc:.1f}%  "
              f"LR={optimizer.param_groups[0]['lr']:.6f}")

        if test_acc > best_acc:
            best_acc = test_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    print(f"\nBest test accuracy: {best_acc:.1f}%")
    return best_state, best_acc


# ============ 主流程 ============
def main():
    print("=" * 60)
    print("  HuBERT 情感分类器训练")
    print("=" * 60)
    print(f"  数据集: {DATA_DIR}")
    print(f"  设备: {DEVICE}")
    print(f"  轮次: {EPOCHS}")
    print()

    # ---- 1. 加载数据 ----
    print("[1/5] 加载数据集...")
    file_paths, labels = [], []
    for idx, emotion in enumerate(EMOTIONS):
        em_dir = DATA_DIR / emotion
        if not em_dir.exists():
            print(f"  [WARN] 目录不存在: {em_dir}")
            continue
        wavs = list(em_dir.glob("*.wav"))
        file_paths.extend(wavs)
        labels.extend([idx] * len(wavs))
        print(f"  {emotion}: {len(wavs)} 条")

    print(f"  总计: {len(file_paths)} 条")

    # 划分训练集/测试集 (80/20)
    train_files, test_files, train_labels, test_labels = train_test_split(
        file_paths, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"  训练集: {len(train_files)}  测试集: {len(test_files)}")

    # ---- 2. 加载 HuBERT ----
    print("\n[2/5] 加载 HuBERT 特征提取器...")
    from transformers import HubertModel, Wav2Vec2FeatureExtractor

    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        "facebook/hubert-base-ls960", local_files_only=True
    )
    hubert = HubertModel.from_pretrained(
        "facebook/hubert-base-ls960", local_files_only=True
    ).to(DEVICE)
    print("  HuBERT 加载完成")

    # ---- 3. 提取特征 ----
    print("\n[3/5] 提取声学特征...")
    train_dataset = CASIADataset(train_files, train_labels)
    test_dataset = CASIADataset(test_files, test_labels)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    t0 = time.time()
    train_feat, train_lbl = extract_features(hubert, processor, train_loader, "训练集特征")
    test_feat, test_lbl = extract_features(hubert, processor, test_loader, "测试集特征")
    print(f"  特征提取完成，耗时 {time.time()-t0:.0f}s")
    print(f"  训练特征: {train_feat.shape}  测试特征: {test_feat.shape}")

    # ---- 4. 训练分类器 ----
    print(f"\n[4/5] 训练分类器 ({EPOCHS} 轮)...")
    feat_train_loader = DataLoader(
        list(zip(train_feat, train_lbl)), batch_size=64, shuffle=True
    )
    feat_test_loader = DataLoader(
        list(zip(test_feat, test_lbl)), batch_size=64, shuffle=False
    )

    best_state, best_acc = train_classifier(feat_train_loader, feat_test_loader)

    # ---- 5. 评估 ----
    print("\n[5/5] 最终评估...")
    clf = EmotionClassifier()
    clf.load_state_dict(best_state)
    clf.eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for features, labels in feat_test_loader:
            outputs = clf(features)
            _, preds = outputs.max(1)
            all_preds.extend(preds.tolist())
            all_labels.extend(labels.tolist())

    print("\n" + classification_report(
        all_labels, all_preds,
        target_names=EMOTIONS,
        digits=3,
    ))

    # 混淆矩阵
    cm = confusion_matrix(all_labels, all_preds)
    print("混淆矩阵:")
    header = "        " + "  ".join(f"{e:4}" for e in EMOTIONS)
    print(header)
    for i, row in enumerate(cm):
        print(f"  {EMOTIONS[i]:4} " + "  ".join(f"{v:4}" for v in row))

    # ---- 保存 ----
    MODEL_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(best_state, MODEL_SAVE_PATH)
    print(f"\n模型已保存到: {MODEL_SAVE_PATH}")
    print(f"声学模型准确率: {best_acc:.1f}%")
    print("重启后端即可使用训练好的声学模型！")


if __name__ == "__main__":
    main()
