# QR Code Generator 🔲✨

live preview
https://piyushkadam96k.github.io/qr-code/

Generate beautiful QR codes with style and flair! 

## ✨ Features
- Generate multiple types of QR codes:
  - URLs 🔗
  - Plain Text 📝
  - WiFi Details 📶
  - Contact Cards (vCard) 👤
  - Email Links 📧
  - SMS Messages 📱
  - Locations 📍
- Stylish module shapes:
  - Square ⬛
  - Rounded ⭕
  - Circle 🔴
  - Star ⭐
  - Diamond 💠
  - Heart ❤️
  - Hexagon 🔷
  - Dots 👾
- Optional center logo embedding 🖼️
- Clean web interface 🎨
- API support (`/api/qr`) 🚀

## 🔧 Prerequisites
- Python 3.8+ 🐍
- Windows OS 🪟

## 💻 Installation
Recommended: Create a virtual environment first!

PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install flask qrcode[pil] pillow
```

CMD:
```cmd
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install flask qrcode[pil] pillow
```

## 🚀 Run (Development)
From project root:
```powershell
python app.py
```
Then visit: http://127.0.0.1:5000 🌐

## 📖 Usage
- Use the web interface to customize your QR code ✨
- Choose type, style, size and optional logo 🎨
- Clean interface with no default URLs 🧹

### 🔌 API Example
```bash
curl -X POST http://127.0.0.1:5000/api/qr \
  -F "qr_type=url" \
  -F "text=https://example.com" \
  -F "style=rounded" \
  -F "box_size=10" \
  -F "border=4" \
  -F "ecc=M"
```
Response: JSON with `img_data` (base64 PNG) and `mime` 📦

## ⚙️ Configuration
- MAX upload: 16MB in `app.py` 📤
- SECRET_KEY: Set via environment variable 🔑

## 🔍 Troubleshooting
- Missing packages? Run `pip install flask qrcode[pil] pillow` 📦
- Upload errors? Check `MAX_CONTENT_LENGTH` 🔧
- Scanner issues? Try 'square' style for best results 🎯

## 🎨 Customization
Edit templates/index.html to modify placeholders and remove any hardcoded URLs 🖌️

## 📄 License
MIT License - Feel free to modify and share! ⚖️

---
Made with ❤️ using Flask and Python 🐍

