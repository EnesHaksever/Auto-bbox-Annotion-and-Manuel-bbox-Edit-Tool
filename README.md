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
