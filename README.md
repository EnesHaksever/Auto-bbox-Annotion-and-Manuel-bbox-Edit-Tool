👇 **Scroll down for Turkish version / Türkçe versiyonu için aşağı kaydırın** 👇

---

# Object Detection Dataset Tool

A desktop application for preparing object detection datasets with YOLO-based automatic labeling and manual editing tools.

## 📋 Overview

This tool provides two different working modes for creating and labeling datasets for your object detection projects:

1. **Auto Label Mode**: Automatically labels images in a folder using the YOLOv8 model
2. **Manual Edit Mode**: Create and edit labels manually with pan/zoom and navigation support

## 🖥️ System Requirements

- **Python**: 3.12
- **Operating System**: Windows, Linux, macOS
- **GPU**: NVIDIA CUDA-capable GPU (recommended) - Also works on CPU
- **CUDA Toolkit**: 12.1 (if using GPU)

## 📦 Dependencies

- `PyQt6` - Desktop GUI
- `ultralytics` - YOLO object detection
- `torch` & `torchvision` - GPU acceleration
- `opencv-python` - Image processing
- `pillow` - Image management
- `numpy` - Numerical operations

## 🚀 Installation Steps

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment
**On Windows:**
```bash
venv\Scripts\activate
```

**On Linux/macOS:**
```bash
source venv/bin/activate
```

### 3. Install Base Libraries
```bash
pip install -r requirements.txt
```

### 4. Install PyTorch and TorchVision for GPU Support
This project is designed for NVIDIA GPU acceleration. Install with CUDA 12.1 support:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Alternative CUDA Versions:**
- CUDA 11.8: Replace with `cu118`
- CPU Mode: Use `https://download.pytorch.org/whl/cpu`

## ▶️ Run the Application

```bash
python main.py
```

The application will open with the PyQt6 desktop interface.

## 📖 User Guide

### Auto Label Mode
1. Select the folder containing your images
2. YOLO model is loaded automatically (takes some time on first run)
3. Each image is processed sequentially:
   - YOLO model performs object detection
   - Filters detections by your specified confidence threshold
   - Saves results to YOLO format `.txt` files

**Output Format**: A `.txt` file with the same name is created for each image:
```
class_id x_center y_center width height
```

### Manual Edit Mode
1. Edit YOLO labels through the visual interface
2. **Pan**: Drag to move the image
3. **Zoom**: Use mouse wheel to zoom in/out
4. **Navigation**: Switch between previous/next images
5. Changes are saved automatically

## 📁 Project Structure

```
OtolabelAndEditing/
├── main.py                 # Main application file
├── requirements.txt        # Python dependencies
├── yolov8n.pt             # YOLO model weights
├── core/
│   ├── detection_engine.py # YOLO detection logic
│   ├── bbox_model.py       # Bounding boxes data model
│   └── yolo_label_parser.py # YOLO file operations
├── ui/
│   ├── main_window.py      # Main window
│   ├── canvas_widget.py    # Drawing canvas
│   └── control_panel.py    # Control panel
└── modes/
    ├── auto_label_mode.py  # Auto labeling
    └── edit_mode.py        # Manual editing
```

## ⚙️ Configuration

You can adjust dependency versions in the `requirements.txt` file as needed.

To tune GPU performance:
- Modify the `confidence` parameter when loading the model (0.0 - 1.0 range)
- Lower value: more detections, higher false positives
- Higher value: fewer detections, only highly confident objects

## 🐛 Troubleshooting

### PyTorch DLL Error
If you get "Error loading c10.dll" error:
1. Uninstall PyTorch: `pip uninstall torch torchvision`
2. Reinstall GPU version: `python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

### Model Loading Error
- First run automatically downloads the YOLOv8n model
- Check your internet connection
- Ensure `yolov8n.pt` file is in the project folder

## 📝 License

This project is open source and uses the Ultralytics YOLO library.

---

# Nesne Tespiti Veri Seti Aracı

YOLO tabanlı otomatik nesne etiketleme ve manuel düzenleme araçlarıyla veri setlerini hazırlayan masaüstü uygulaması.

## 📋 Genel Bakış

Bu araç, nesne tespiti projeleriniz için veri seti oluşturmada ve etiketlemede iki farklı çalışma modu sunmaktadır:

1. **Otomatik Etiketleme Modu**: YOLOv8 modelini kullanarak klasördeki görselleri otomatik olarak etiketler
2. **Manuel Düzenleme Modu**: Etiketleri manuel olarak oluşturup düzenleyin, pan/zoom ve navigasyon desteğiyle

## 🖥️ Sistem Gereksinimleri

- **Python**: 3.12
- **İşletim Sistemi**: Windows, Linux, macOS
- **GPU**: NVIDIA CUDA desteğine sahip GPU (önerilir) - CPU'da da çalışır
- **CUDA Toolkit**: 12.1 (GPU kullanacaksanız)

## 📦 Bağımlılıklar

- `PyQt6` - Masaüstü arayüzü
- `ultralytics` - YOLO nesne tespiti
- `torch` & `torchvision` - GPU hızlandırması
- `opencv-python` - Görüntü işleme
- `pillow` - Görüntü yönetimi
- `numpy` - Sayısal işlemler

## 🚀 Kurulum Adımları

### 1. Sanal Ortam Oluştur
```bash
python -m venv venv
```

### 2. Sanal Ortamı Etkinleştir
**Windows'ta:**
```bash
venv\Scripts\activate
```

**Linux/macOS'ta:**
```bash
source venv/bin/activate
```

### 3. Temel Kütüphaneleri Yükle
```bash
pip install -r requirements.txt
```

### 4. GPU Desteği için PyTorch ve TorchVision Yükle
Bu proje NVIDIA GPU hızlandırması için tasarlanmıştır. CUDA 12.1 desteğiyle yükleyin:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Alternatif CUDA Sürümleri:**
- CUDA 11.8: `cu118` yerine koyun
- CPU Modu: `https://download.pytorch.org/whl/cpu` kullanın

## ▶️ Uygulamayı Çalıştır

```bash
python main.py
```

Uygulama PyQt6 masaüstü arayüzüyle açılacaktır.

## 📖 Kullanım Kılavuzu

### Otomatik Etiketleme Modu (Auto Label Mode)
1. Görsellerin bulunduğu klasörü seçin
2. YOLO modeli otomatik olarak yüklenir (ilk kez biraz zaman alabilir)
3. Her görsel sırayla işlenir:
   - YOLO modeli nesne tespiti yapar
   - Tespit edilen nesneleri belirttiğiniz güven (confidence) eşiğine göre filtreler
   - Sonuçları YOLO formatında `.txt` dosyalarına kaydeder

**Çıkış Format**: Her görsel için aynı isimde `.txt` dosyası oluşturulur:
```
class_id x_center y_center width height
```

### Manuel Düzenleme Modu (Edit Mode)
1. YOLO etiketlerini görsel arayüzü üzerinde düzenleyin
2. **Pan**: Görüntüyü hareket ettirmek için sürükleyin
3. **Zoom**: Fare tekerleği ile yaklaş/uzaklaş
4. **Navigasyon**: Önceki/sonraki görsel arasında geç
5. Değişiklikleri otomatik olarak kaydedilir

## 📁 Proje Yapısı

```
OtolabelAndEditing/
├── main.py                 # Ana uygulama dosyası
├── requirements.txt        # Python bağımlılıkları
├── yolov8n.pt             # YOLO model ağırlıkları
├── core/
│   ├── detection_engine.py # YOLO tespiti mantığı
│   ├── bbox_model.py       # Sınırlayıcı kutular veri modeli
│   └── yolo_label_parser.py # YOLO dosya işlemleri
├── ui/
│   ├── main_window.py      # Ana pencere
│   ├── canvas_widget.py    # Çizim alanı
│   └── control_panel.py    # Kontrol paneli
└── modes/
    ├── auto_label_mode.py  # Otomatik etiketleme
    └── edit_mode.py        # Manuel düzenleme
```

## ⚙️ Yapılandırma

`requirements.txt` dosyasında bağımlılık sürümlerini ihtiyaca göre düzenleyebilirsiniz.

GPU performansını ayarlamak için:
- Modeli yüklenirken `confidence` parametresini değiştirin (0.0 - 1.0 arası)
- Düşük değer: daha fazla tespit, yanlış pozitifleri yüksek
- Yüksek değer: daha az tespit, yalnızca kesinlikli nesneler

## 🐛 Sorun Giderme

### PyTorch DLL Hatası
Eğer "Error loading c10.dll" hatası alırsanız:
1. PyTorch'u kaldırın: `pip uninstall torch torchvision`
2. GPU versiyonunu yeniden yükleyin: `python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

### Model Yükleme Hatası
- İlk çalıştırmada YOLOv8n modelini otomatik indirir
- İnternet bağlantınızı kontrol edin
- `yolov8n.pt` dosyasının proje klasöründe olduğundan emin olun

## 📝 Lisans

Bu proje açık kaynak kodludur. Ultralytics YOLO kütüphanesinden yararlanır.
