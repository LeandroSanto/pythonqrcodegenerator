from flask import Flask, request, send_file
import qrcode
import io
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont  # Adições para manipulação de imagem e texto

app = Flask(__name__)
executor = ThreadPoolExecutor(2)  # Pool de 2 threads

# Configurações do texto
FONT_SIZE = 16
TEXT_PADDING = 10
BACKGROUND_COLOR = 'white'
TEXT_COLOR = 'black'

def generate_qr_image(data):
    # Gerar o QR code (parte original)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Converter para PIL Image se não for já
    qr_img = qr_img.get_image() if hasattr(qr_img, 'get_image') else qr_img
    
    # Adicionar texto abaixo do QR code (nova parte)
    try:
        # Tentar carregar fonte padrão do sistema
        try:
            font = ImageFont.truetype("arial.ttf", FONT_SIZE)
        except:
            font = ImageFont.load_default()
        
        # Calcular tamanho necessário para o texto
        dummy_img = Image.new('RGB', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        text_width = dummy_draw.textlength(data, font=font)
        
        # Criar nova imagem com espaço para o texto
        new_width = max(qr_img.width, int(text_width) + 2 * TEXT_PADDING)
        new_height = qr_img.height + FONT_SIZE + 3 * TEXT_PADDING
        new_img = Image.new('RGB', (new_width, new_height), BACKGROUND_COLOR)
        
        # Colar o QR code na nova imagem
        qr_position = ((new_img.width - qr_img.width) // 2, TEXT_PADDING)
        new_img.paste(qr_img, qr_position)
        
        # Adicionar o texto
        draw = ImageDraw.Draw(new_img)
        text_position = (
            (new_img.width - text_width) // 2,
            qr_img.height + 2 * TEXT_PADDING
        )
        draw.text(text_position, data, font=font, fill=TEXT_COLOR)
        
        # Salvar em BytesIO
        img_io = io.BytesIO()
        new_img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io
        
    except Exception as e:
        # Fallback: retornar apenas o QR code se houver erro na adição do texto
        img_io = io.BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        return img_io

@app.route('/api/generate-qr', methods=['GET'])
def generate_qr():
    data = request.args.get('data')
    if not data:
        return {"error": "Parâmetro 'data' é obrigatório"}, 400
    
    try:
        img_io = executor.submit(generate_qr_image, data).result()
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, threaded=True, debug=True)