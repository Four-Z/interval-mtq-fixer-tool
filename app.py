from flask import Flask, request, jsonify

app = Flask(__name__)


def is_valid_combination(seq, max_interval):
    # Periksa jarak antar angka dalam kombinasi
    differences = [abs(seq[j] - seq[i]) for i in range(len(seq))
                   for j in range(i+1, len(seq))]
    return all(diff <= max_interval for diff in differences)


def solve_interval(scores, max_interval):
    """
    Menyelesaikan masalah interval penilaian juri.

    Args:
        scores: Dictionary berisi nilai dari ketiga juri {'Hakim 1': nilai1, 'Hakim 2': nilai2, 'Hakim 3': nilai3}
        max_interval: Nilai interval maksimal yang diperbolehkan

    Returns:
        Dictionary berisi nilai yang sudah disesuaikan {'Hakim 1': nilai1_baru, 'Hakim 2': nilai2_baru, 'Hakim 3': nilai3_baru}
    """
    # Membuat salinan nilai asli
    adjusted_scores = scores.copy()

    # Konversi dictionary ke list untuk memudahkan pengolahan
    hakim_names = list(scores.keys())
    scores_list = [scores[name] for name in hakim_names]

    # Cek apakah sudah valid
    if is_valid_combination(scores_list, max_interval):
        return adjusted_scores, "Nilai sudah valid, tidak perlu penyesuaian"

    # Dapatkan nilai-nilai untuk analisis
    sorted_pairs = sorted(zip(hakim_names, scores_list),
                          key=lambda x: x[1], reverse=True)
    sorted_hakim = [pair[0] for pair in sorted_pairs]
    sorted_scores = [pair[1] for pair in sorted_pairs]

    highest_name, highest = sorted_hakim[0], sorted_scores[0]
    middle_name, middle = sorted_hakim[1], sorted_scores[1]
    lowest_name, lowest = sorted_hakim[2], sorted_scores[2]

    # Hitung interval
    interval_high = highest - middle
    interval_low = middle - lowest
    interval_total = highest - lowest

    # Implementasi Aturan 1: Dua juri memberi nilai sama, satu berbeda
    if abs(highest - middle) < 0.001:  # Nilai tertinggi dan tengah sama
        if interval_low > max_interval:
            adjusted_scores[lowest_name] = highest - max_interval
            return adjusted_scores, f"Aturan 1: Dua hakim memberi nilai sama di atas. {lowest_name} dinaikkan."

    if abs(middle - lowest) < 0.001:  # Nilai tengah dan terendah sama
        if interval_high > max_interval:
            adjusted_scores[highest_name] = lowest + max_interval
            return adjusted_scores, f"Aturan 1: Dua hakim memberi nilai sama di bawah. {highest_name} diturunkan."

    # Implementasi Aturan 2: Interval atas dan bawah sama
    if abs(interval_high - interval_low) < 0.001:
        # Gunakan max_interval / 2
        adjustment = max_interval / 2
        adjusted_scores[highest_name] = middle + adjustment
        # Nilai tengah tetap
        adjusted_scores[lowest_name] = middle - adjustment
        return adjusted_scores, f"Aturan 2: Interval atas dan bawah sama. {highest_name} diturunkan dan {lowest_name} dinaikkan."

    # Implementasi Aturan 3: 2 nilai tidak memiliki interval (dalam batas maksimal interval) dan nilai ke-3 terlalu rendah atau terlalu tinggi, maka hanya nilai ke-3 yang disesuaikan.
    # Dua teratas dekat, lowest terlalu rendah
    if interval_high <= max_interval and interval_total > max_interval:
        if interval_high >= max_interval / 2:
            adjusted_scores[highest_name] = middle + max_interval/2
            adjusted_scores[lowest_name] = adjusted_scores[highest_name] - max_interval
        else:
            adjusted_scores[lowest_name] = highest - max_interval
        return adjusted_scores, f"Aturan 3: Dua nilai teratas tidak memiliki interval. {lowest_name} dinaikkan."
    # Dua terbawah dekat, highest terlalu tinggi
    elif interval_low <= max_interval and interval_total > max_interval:
        if interval_low >= max_interval / 2:
            adjusted_scores[lowest_name] = middle - max_interval/2
            adjusted_scores[highest_name] = adjusted_scores[lowest_name] + max_interval
        else:
            adjusted_scores[highest_name] = lowest + max_interval
        return adjusted_scores, f"Aturan 3: Dua nilai terbawah tidak memiliki interval. {highest_name} diturunkan."

    # Implementasi Aturan 4: Interval atas dan bawah berbeda, nilai tengah sebagai acuan
    if scores_list.count(middle) == 1:  # Hanya ada satu nilai tengah
        half_max_interval = max_interval / 2
        adjusted_scores[highest_name] = middle + half_max_interval
        adjusted_scores[lowest_name] = middle - half_max_interval
        return adjusted_scores, f"Aturan 4: Interval atas dan bawah berbeda. Nilai tengah ({middle_name}) dijadikan acuan."

    # Jika tidak ada aturan yang tepat, gunakan pendekatan umum
    if interval_total > max_interval:
        ideal_middle = (highest + lowest) / 2
        half_max_interval = max_interval / 2

        adjusted_scores[highest_name] = ideal_middle + half_max_interval
        adjusted_scores[lowest_name] = ideal_middle - half_max_interval
        return adjusted_scores, "Aturan umum: Sesuaikan nilai tertinggi dan terendah ke nilai tengah ideal."

    return adjusted_scores, "Tidak ada penyesuaian yang diperlukan."


def format_nilai(nilai):
    """Format nilai dengan tiga digit desimal"""
    return round(float(nilai), 3)


@app.route('/api/check-interval', methods=['POST'])
def check_interval():
    try:
        data = request.get_json()

        # Validasi request
        required_fields = ['hakim1', 'hakim2',
                           'hakim3', 'max_nilai', 'max_interval']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required_fields': required_fields
            }), 400

        # Ekstrak nilai
        hakim1 = float(data['hakim1'])
        hakim2 = float(data['hakim2'])
        hakim3 = float(data['hakim3'])
        max_nilai = float(data['max_nilai'])
        max_interval = float(data['max_interval'])

        # Validasi nilai
        if any(nilai < 0 or nilai > max_nilai for nilai in [hakim1, hakim2, hakim3]):
            return jsonify({
                'error': f'Nilai harus antara 0 dan {max_nilai}'
            }), 400

        input_nilai = {
            "Hakim 1": hakim1,
            "Hakim 2": hakim2,
            "Hakim 3": hakim3
        }

        # Cek apakah interval valid
        is_valid = is_valid_combination(
            list(input_nilai.values()), max_interval)

        nilai_list = list(input_nilai.values())
        nilai_list.sort(reverse=True)
        original_interval = nilai_list[0] - nilai_list[-1]

        response = {
            'hakim_values': {
                'original': {k: format_nilai(v) for k, v in input_nilai.items()}
            },
            'original_interval': format_nilai(original_interval),
            'max_interval': max_interval,
            'is_valid': is_valid
        }

        if not is_valid:
            # Lakukan penyesuaian
            adjusted_nilai, rule_applied = solve_interval(
                input_nilai, max_interval)

            # Hitung interval baru
            adjusted_list = list(adjusted_nilai.values())
            adjusted_list.sort(reverse=True)
            new_interval = adjusted_list[0] - adjusted_list[-1]

            response.update({
                'hakim_values': {
                    'original': {k: format_nilai(v) for k, v in input_nilai.items()},
                    'adjusted': {k: format_nilai(v) for k, v in adjusted_nilai.items()}
                },
                'rule_applied': rule_applied,
                'new_interval': format_nilai(new_interval)
            })

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/interval-config', methods=['GET'])
def get_interval_config():
    """Endpoint untuk mendapatkan konfigurasi interval yang tersedia"""
    configs = [
        {"max_nilai": 15.0, "max_interval": 0.75},
        {"max_nilai": 20.0, "max_interval": 1.0},
        {"max_nilai": 25.0, "max_interval": 1.25},
        {"max_nilai": 30.0, "max_interval": 1.5},
        {"max_nilai": 40.0, "max_interval": 2.0},
        {"max_nilai": 50.0, "max_interval": 2.5},
        {"max_nilai": 100.0, "max_interval": 5.0},
    ]
    return jsonify(configs)


@app.route('/', methods=['GET'])
def index():
    """Endpoint untuk dokumentasi API sederhana"""
    return """
    <html>
    <head>
        <title>Interval Fixer API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Interval Fixer API</h1>
        <p>API untuk memeriksa dan memperbaiki interval nilai tiga hakim.</p>
        
        <h2>Endpoints</h2>
        
        <h3>GET /api/interval-config</h3>
        <p>Mendapatkan daftar konfigurasi yang tersedia</p>
        <p>Response:</p>
        <pre>
[
    {"max_nilai": 15.0, "max_interval": 0.75},
    {"max_nilai": 20.0, "max_interval": 1.0},
    ...
]
        </pre>
        
        <h3>POST /api/check-interval</h3>
        <p>Memeriksa dan memperbaiki interval nilai</p>
        <p>Request:</p>
        <pre>
{
    "hakim1": 15.0,
    "hakim2": 14.0,
    "hakim3": 13.0,
    "max_nilai": 15.0,
    "max_interval": 0.75
}
        </pre>
        <p>Response jika valid:</p>
        <pre>
{
    "hakim_values": {
        "original": {
            "Hakim 1": 15.0,
            "Hakim 2": 14.0,
            "Hakim 3": 13.0
        }
    },
    "original_interval": 2.0,
    "max_interval": 0.75,
    "is_valid": false
}
        </pre>
        <p>Response jika tidak valid:</p>
        <pre>
{
    "hakim_values": {
        "original": {
            "Hakim 1": 15.0,
            "Hakim 2": 14.0,
            "Hakim 3": 13.0
        },
        "adjusted": {
            "Hakim 1": 14.375,
            "Hakim 2": 14.0,
            "Hakim 3": 13.625
        }
    },
    "rule_applied": "Aturan 4: Interval atas dan bawah berbeda. Nilai tengah (Hakim 2) dijadikan acuan.",
    "original_interval": 2.0,
    "new_interval": 0.75,
    "max_interval": 0.75,
    "is_valid": false
}
        </pre>
    </body>
    </html>
    """
