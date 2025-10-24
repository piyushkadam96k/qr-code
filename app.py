from flask import Flask, render_template, request, jsonify, abort
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image, ImageDraw
import io
import base64
import math
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

ECC_MAP = {
    'L': ERROR_CORRECT_L,
    'M': ERROR_CORRECT_M,
    'Q': ERROR_CORRECT_Q,
    'H': ERROR_CORRECT_H,
}

def make_star_points(cx, cy, r_out, r_in, points=5):
    pts = []
    for i in range(points * 2):
        angle = math.pi * i / points
        r = r_out if i % 2 == 0 else r_in
        x = cx + math.cos(angle) * r
        y = cy - math.sin(angle) * r
        pts.append((x, y))
    return pts

def render_matrix_to_image(matrix, box_size, border, style):
    # fixed colors: black modules on white background
    FG = (0, 0, 0, 255)
    BG = (255, 255, 255, 255)

    modules_y = len(matrix)
    modules_x = len(matrix[0])
    size_x = (modules_x + border * 2) * box_size
    size_y = (modules_y + border * 2) * box_size

    img = Image.new("RGBA", (size_x, size_y), BG)
    draw = ImageDraw.Draw(img)

    for r in range(modules_y):
        for c in range(modules_x):
            if not matrix[r][c]:
                continue
            x0 = (c + border) * box_size
            y0 = (r + border) * box_size
            x1 = x0 + box_size
            y1 = y0 + box_size

            # Keep finder patterns as squares (approx 7x7)
            is_finder = (
                (r < 7 and c < 7) or
                (r < 7 and c >= modules_x - 7) or
                (r >= modules_y - 7 and c < 7)
            )

            if is_finder:
                draw.rectangle([x0, y0, x1, y1], fill=FG)
            elif style == 'square':
                draw.rectangle([x0, y0, x1, y1], fill=FG)
            elif style == 'rounded':
                radius = int(box_size * 0.25)
                try:
                    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=FG)
                except Exception:
                    draw.rectangle([x0, y0, x1, y1], fill=FG)
            elif style == 'circle':
                draw.ellipse([x0, y0, x1, y1], fill=FG)
            elif style == 'star':
                cx = (x0 + x1) / 2
                cy = (y0 + y1) / 2
                r_out = box_size * 0.48
                r_in = r_out * 0.45
                pts = make_star_points(cx, cy, r_out, r_in)
                draw.polygon(pts, fill=FG)
            elif style == 'diamond':
                pts = [
                    ((x0 + x1) / 2, y0),  # top
                    (x1, (y0 + y1) / 2),  # right
                    ((x0 + x1) / 2, y1),  # bottom
                    (x0, (y0 + y1) / 2)   # left
                ]
                draw.polygon(pts, fill=FG)
            elif style == 'heart':
                # Simple heart shape
                cx = (x0 + x1) / 2
                cy = (y0 + y1) / 2
                size = box_size * 0.4
                draw.ellipse([cx - size, y0, cx, cy], fill=FG)
                draw.ellipse([cx, y0, cx + size, cy], fill=FG)
                pts = [
                    (cx - size, cy - size/2),
                    (cx + size, cy - size/2),
                    (cx, y1)
                ]
                draw.polygon(pts, fill=FG)
            elif style == 'hexagon':
                size = box_size * 0.5
                cx = (x0 + x1) / 2
                cy = (y0 + y1) / 2
                pts = []
                for i in range(6):
                    angle = i * math.pi / 3
                    pts.append((
                        cx + size * math.cos(angle),
                        cy + size * math.sin(angle)
                    ))
                draw.polygon(pts, fill=FG)
            else:
                draw.rectangle([x0, y0, x1, y1], fill=FG)

    return img

def validate_inputs(text, box_size, border, ecc_key, style):
    """Validate input parameters"""
    if not text or len(text.strip()) == 0:
        raise ValueError("Text cannot be empty")
    
    if len(text) > 10000:  # Reasonable limit for QR codes
        raise ValueError("Text is too long (max 10,000 characters)")
    
    if not (1 <= box_size <= 50):
        raise ValueError("Box size must be between 1 and 50")
    
    if not (0 <= border <= 20):
        raise ValueError("Border must be between 0 and 20")
    
    if ecc_key not in ECC_MAP:
        raise ValueError("Invalid error correction level")
    
    valid_styles = ['square', 'rounded', 'circle', 'star', 'diamond', 'heart', 'hexagon']
    if style not in valid_styles:
        raise ValueError("Invalid style")

def generate_wifi_qr(ssid, password, security):
    """Generate WiFi QR code string"""
    if security == "nopass":
        return f"WIFI:T:nopass;S:{ssid};;"
    else:
        return f"WIFI:T:{security};S:{ssid};P:{password};H:false;;"

def generate_vcard_qr(name, phone, email, company):
    """Generate vCard QR code string"""
    vcard = "BEGIN:VCARD\nVERSION:3.0\n"
    if name:
        vcard += f"FN:{name}\n"
    if phone:
        vcard += f"TEL:{phone}\n"
    if email:
        vcard += f"EMAIL:{email}\n"
    if company:
        vcard += f"ORG:{company}\n"
    vcard += "END:VCARD"
    return vcard

def generate_email_qr(to_email, subject, body):
    """Generate email QR code string"""
    email_data = f"mailto:{to_email}"
    params = []
    if subject:
        params.append(f"subject={subject}")
    if body:
        params.append(f"body={body}")
    if params:
        email_data += "?" + "&".join(params)
    return email_data

def generate_sms_qr(phone, message):
    """Generate SMS QR code string"""
    sms_data = f"sms:{phone}"
    if message:
        sms_data += f":{message}"
    return sms_data

def generate_location_qr(lat, lng, name):
    """Generate location QR code string"""
    location_data = f"geo:{lat},{lng}"
    if name:
        location_data += f"?q={name}"
    return location_data

def generate_qr_image_bytes(text, box_size, border, ecc, style, logo_file=None):
    # Get the ecc_key for validation
    ecc_key = None
    for key, value in ECC_MAP.items():
        if value == ecc:
            ecc_key = key
            break
    
    # Validate inputs
    validate_inputs(text, box_size, border, ecc_key, style)
    
    try:
        qr = qrcode.QRCode(
            error_correction=ecc,
            box_size=box_size,
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)
        matrix = qr.get_matrix()  # 2D boolean matrix

        img = render_matrix_to_image(matrix, box_size, border, style).convert("RGBA")

        # optional logo with better error handling
        if logo_file and getattr(logo_file, "filename", ""):
            try:
                # Validate file type
                filename = secure_filename(logo_file.filename)
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    raise ValueError("Logo must be a PNG or JPG file")
                
                logo = Image.open(logo_file.stream).convert("RGBA")
                
                # Validate logo size
                if logo.size[0] > 2000 or logo.size[1] > 2000:
                    raise ValueError("Logo is too large (max 2000x2000 pixels)")
                
                qr_w, qr_h = img.size
                max_logo = int(min(qr_w, qr_h) * 0.22)
                logo.thumbnail((max_logo, max_logo), Image.LANCZOS)
                lx, ly = logo.size
                pos = ((qr_w - lx) // 2, (qr_h - ly) // 2)
                img.paste(logo, pos, logo)
            except Exception as e:
                raise ValueError(f"Error processing logo: {str(e)}")

        buf = io.BytesIO()
        img.save(buf, format='PNG', optimize=True)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        raise ValueError(f"Error generating QR code: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    img_data = None
    mime = None
    error = None
    
    if request.method == 'POST':
        try:
            qr_type = request.form.get('qr_type', 'url')
            box_size = int(request.form.get('box_size', 10))
            border = int(request.form.get('border', 4))
            ecc_key = request.form.get('ecc', 'M')
            ecc = ECC_MAP.get(ecc_key, ERROR_CORRECT_M)
            style = request.form.get('style', 'square')
            
            # Generate QR data based on type
            qr_data = ""
            
            if qr_type == 'url':
                qr_data = request.form.get('text', '').strip()
                if not qr_data:
                    error = "Please enter a website URL."
            elif qr_type == 'text':
                qr_data = request.form.get('text_content', '').strip()
                if not qr_data:
                    error = "Please enter text content."
            elif qr_type == 'wifi':
                ssid = request.form.get('wifi_ssid', '').strip()
                if not ssid:
                    error = "Please enter WiFi network name."
                else:
                    password = request.form.get('wifi_password', '').strip()
                    security = request.form.get('wifi_security', 'WPA')
                    qr_data = generate_wifi_qr(ssid, password, security)
            elif qr_type == 'contact':
                name = request.form.get('contact_name', '').strip()
                if not name:
                    error = "Please enter contact name."
                else:
                    phone = request.form.get('contact_phone', '').strip()
                    email = request.form.get('contact_email', '').strip()
                    company = request.form.get('contact_company', '').strip()
                    qr_data = generate_vcard_qr(name, phone, email, company)
            elif qr_type == 'email':
                to_email = request.form.get('email_to', '').strip()
                if not to_email:
                    error = "Please enter recipient email."
                else:
                    subject = request.form.get('email_subject', '').strip()
                    body = request.form.get('email_body', '').strip()
                    qr_data = generate_email_qr(to_email, subject, body)
            elif qr_type == 'sms':
                phone = request.form.get('sms_number', '').strip()
                if not phone:
                    error = "Please enter phone number."
                else:
                    message = request.form.get('sms_message', '').strip()
                    qr_data = generate_sms_qr(phone, message)
            elif qr_type == 'phone':
                phone = request.form.get('phone_number', '').strip()
                if not phone:
                    error = "Please enter phone number."
                else:
                    qr_data = f"tel:{phone}"
            elif qr_type == 'location':
                lat = request.form.get('location_lat', '').strip()
                lng = request.form.get('location_lng', '').strip()
                if not lat or not lng:
                    error = "Please enter both latitude and longitude."
                else:
                    name = request.form.get('location_name', '').strip()
                    qr_data = generate_location_qr(lat, lng, name)
            
            if not error and qr_data:
                data = generate_qr_image_bytes(qr_data, box_size, border, ecc, style, request.files.get('logo'))
                img_data = base64.b64encode(data).decode('ascii')
                mime = 'image/png'
                
        except ValueError as ve:
            error = str(ve)
        except Exception as exc:
            error = f"An unexpected error occurred: {str(exc)}"
    else:
        # Don't generate any default QR code on page load
        return render_template('index.html', img_data=None, mime=None, error=None)

    return render_template('index.html', img_data=img_data, mime=mime, error=error)

@app.route('/api/qr', methods=['POST'])
def api_qr():
    try:
        qr_type = request.form.get('qr_type', 'url')
        box_size = int(request.form.get('box_size', 10))
        border = int(request.form.get('border', 4))
        ecc_key = request.form.get('ecc', 'M')
        ecc = ECC_MAP.get(ecc_key, ERROR_CORRECT_M)
        style = request.form.get('style', 'square')
        
        # Generate QR data based on type (same logic as main route)
        qr_data = ""
        
        if qr_type == 'url':
            qr_data = request.form.get('text', '').strip()
            if not qr_data:
                return jsonify({"error": "Please enter a website URL."}), 400
        elif qr_type == 'text':
            qr_data = request.form.get('text_content', '').strip()
            if not qr_data:
                return jsonify({"error": "Please enter text content."}), 400
        elif qr_type == 'wifi':
            ssid = request.form.get('wifi_ssid', '').strip()
            if not ssid:
                return jsonify({"error": "Please enter WiFi network name."}), 400
            password = request.form.get('wifi_password', '').strip()
            security = request.form.get('wifi_security', 'WPA')
            qr_data = generate_wifi_qr(ssid, password, security)
        elif qr_type == 'contact':
            name = request.form.get('contact_name', '').strip()
            if not name:
                return jsonify({"error": "Please enter contact name."}), 400
            phone = request.form.get('contact_phone', '').strip()
            email = request.form.get('contact_email', '').strip()
            company = request.form.get('contact_company', '').strip()
            qr_data = generate_vcard_qr(name, phone, email, company)
        elif qr_type == 'email':
            to_email = request.form.get('email_to', '').strip()
            if not to_email:
                return jsonify({"error": "Please enter recipient email."}), 400
            subject = request.form.get('email_subject', '').strip()
            body = request.form.get('email_body', '').strip()
            qr_data = generate_email_qr(to_email, subject, body)
        elif qr_type == 'sms':
            phone = request.form.get('sms_number', '').strip()
            if not phone:
                return jsonify({"error": "Please enter phone number."}), 400
            message = request.form.get('sms_message', '').strip()
            qr_data = generate_sms_qr(phone, message)
        elif qr_type == 'phone':
            phone = request.form.get('phone_number', '').strip()
            if not phone:
                return jsonify({"error": "Please enter phone number."}), 400
            qr_data = f"tel:{phone}"
        elif qr_type == 'location':
            lat = request.form.get('location_lat', '').strip()
            lng = request.form.get('location_lng', '').strip()
            if not lat or not lng:
                return jsonify({"error": "Please enter both latitude and longitude."}), 400
            name = request.form.get('location_name', '').strip()
            qr_data = generate_location_qr(lat, lng, name)
        
        data = generate_qr_image_bytes(qr_data, box_size, border, ecc, style, request.files.get('logo'))
        return jsonify({"img_data": base64.b64encode(data).decode('ascii'), "mime": "image/png"})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as exc:
        return jsonify({"error": f"An unexpected error occurred: {str(exc)}"}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16MB."}), 413

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request."}), 400

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)