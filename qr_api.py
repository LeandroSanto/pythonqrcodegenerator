from flask import Flask, request, send_file
import qrcode
import io
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
executor = ThreadPoolExecutor(2)

# Configurações do texto
FONT_SIZE = 16
TEXT_PADDING = 10
BACKGROUND_COLOR = 'white'
TEXT_COLOR = 'black'

def generate_qr_image(data, text):
    # Gerar o QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.get_image() if hasattr(qr_img, 'get_image') else qr_img

    try:
        # Fonte
        try:
            font = ImageFont.truetype("arial.ttf", FONT_SIZE)
        except:
            font = ImageFont.load_default()

        # Criar imagem para medir texto
        dummy_img = Image.new('RGB', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        data_width = dummy_draw.textlength(data, font=font)
        text_width = dummy_draw.textlength(text, font=font)

        total_width = max(qr_img.width, int(data_width), int(text_width)) + 2 * TEXT_PADDING
        total_height = (
            qr_img.height +
            TEXT_PADDING +
            FONT_SIZE +  # altura do data
            TEXT_PADDING +
            FONT_SIZE +  # altura do texto
            TEXT_PADDING
        )

        # Nova imagem
        new_img = Image.new('RGB', (total_width, total_height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(new_img)

        # Posições
        qr_pos = ((total_width - qr_img.width) // 2, TEXT_PADDING)
        data_pos = ((total_width - data_width) // 2, qr_pos[1] + qr_img.height + TEXT_PADDING)
        text_pos = ((total_width - text_width) // 2, data_pos[1] + FONT_SIZE + TEXT_PADDING)

        # Compor imagem
        new_img.paste(qr_img, qr_pos)
        draw.text(data_pos, data, font=font, fill=TEXT_COLOR)
        draw.text(text_pos, text, font=font, fill=TEXT_COLOR)

        # Salvar imagem
        img_io = io.BytesIO()
        new_img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io

    except Exception as e:
        # Fallback
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io

@app.route('/api/generate-qr', methods=['GET'])
def generate_qr():
    data = request.args.get('data')
    text = request.args.get('text')
    if not data:
        return {"error": "Parâmetro 'data' é obrigatório"}, 400
    if not text:
        return {"error": "Parâmetro 'text' é obrigatório"}, 400
    try:
        img_io = executor.submit(generate_qr_image, data, text).result()
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, threaded=True, debug=True)
