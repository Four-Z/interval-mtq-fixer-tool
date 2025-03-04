import streamlit as st
import pandas as pd
import numpy as np


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
        # Gunakan max_interval / 2 * 1.2 untuk sesuaikan nilai
        adjustment = max_interval / 2 * 1.2
        adjusted_scores[highest_name] = highest - adjustment
        # Nilai tengah tetap
        adjusted_scores[lowest_name] = lowest + adjustment
        return adjusted_scores, f"Aturan 2: Interval atas dan bawah sama. {highest_name} diturunkan dan {lowest_name} dinaikkan."

    # Implementasi Aturan 3: Interval atas dan bawah berbeda, nilai tengah sebagai acuan
    if scores_list.count(middle) == 1:  # Hanya ada satu nilai tengah
        half_max_interval = max_interval / 2
        adjusted_scores[highest_name] = middle + half_max_interval
        adjusted_scores[lowest_name] = middle - half_max_interval
        return adjusted_scores, f"Aturan 3: Interval atas dan bawah berbeda. Nilai tengah ({middle_name}) dijadikan acuan."

    # Implementasi Aturan 4: Dua nilai teratas tidak memiliki interval (≤ max_interval)
    if interval_high <= max_interval and interval_low > max_interval:
        adjusted_scores[lowest_name] = highest - max_interval
        return adjusted_scores, f"Aturan 4: Dua nilai teratas tidak memiliki interval. {lowest_name} dinaikkan."

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
    return f"{nilai:.3f}"


def main():
    st.title('Interval Fixer Tool')
    st.write(
        "Alat untuk memperbaiki nilai hakim yang memiliki interval melebihi batas maksimal")

    # Tambahkan informasi tentang aturan yang digunakan
    with st.expander("Informasi Aturan Penyesuaian"):
        st.markdown(f"""
        ### Aturan Penyesuaian Nilai
        
        1. **Aturan 1**: Jika 2 hakim memberikan nilai sama dan 1 hakim berbeda dengan interval > maksimal interval, maka nilai hakim yang berbeda disesuaikan.
        
        2. **Aturan 2**: Jika interval atas dan bawah sama, maka nilai tertinggi dikurangi dan nilai terendah ditambah dengan proporsi yang sesuai dengan max interval.
        
        3. **Aturan 3**: Jika interval atas dan bawah berbeda dengan nilai tengah sebagai acuan, maka:
           - Nilai tertinggi = nilai tengah + (maksimal interval/2)
           - Nilai tengah tetap
           - Nilai terendah = nilai tengah - (maksimal interval/2)
        
        4. **Aturan 4**: Jika 2 nilai teratas tidak memiliki interval (dalam batas maksimal interval) dan nilai ke-3 terlalu rendah, maka hanya nilai ke-3 yang disesuaikan.
        """)

    options = (
        "Max Nilai: 25 | Max Interval: 1.25",
        "Max Nilai: 50 | Max Interval: 2.5",
        "Max Nilai: 100 | Max Interval: 5.0",
    )

    option = st.selectbox("Pilih Max Nilai & Interval", options)

    # Mendapatkan index dari opsi yang dipilih
    index = options.index(option)

    if index == 0:
        max_nilai, max_interval = 25.0, 1.25
    elif index == 1:
        max_nilai, max_interval = 50.0, 2.5
    elif index == 2:
        max_nilai, max_interval = 100.0, 5.0

    st.write(f"Max Nilai: {max_nilai} | Max Interval: {max_interval}")

    # Buat kolom untuk input nilai
    col1, col2, col3 = st.columns(3)

    with col1:
        input_nilai_1 = st.number_input(
            'Masukkan Nilai Hakim 1', value=0.00, step=0.25, max_value=float(max_nilai), min_value=0.0, format="%.2f")

    with col2:
        input_nilai_2 = st.number_input(
            'Masukkan Nilai Hakim 2', value=0.00, step=0.25, max_value=float(max_nilai), min_value=0.0, format="%.2f")

    with col3:
        input_nilai_3 = st.number_input(
            'Masukkan Nilai Hakim 3', value=0.00, step=0.25, max_value=float(max_nilai), min_value=0.0, format="%.2f")

    input_nilai = {
        "Hakim 1": input_nilai_1,
        "Hakim 2": input_nilai_2,
        "Hakim 3": input_nilai_3
    }

    if st.button('Periksa dan Perbaiki Interval'):
        # Periksa apakah semua nilai sudah diisi
        if all(nilai > 0 for nilai in input_nilai.values()):
            # Cek apakah interval valid
            is_valid = is_valid_combination(
                list(input_nilai.values()), max_interval)

            if is_valid:
                st.success("Interval sudah valid! Tidak perlu penyesuaian.")

                # Tampilkan tabel nilai
                df = pd.DataFrame({
                    "Hakim": list(input_nilai.keys()),
                    "Nilai": [format_nilai(nilai) for nilai in input_nilai.values()]
                })
                st.table(df)

                # Hitung dan tampilkan interval
                nilai_list = list(input_nilai.values())
                nilai_list.sort(reverse=True)
                st.write(
                    f"Interval tertinggi-terendah: {format_nilai(nilai_list[0] - nilai_list[-1])}")

            else:
                st.warning(
                    "Interval melebihi batas maksimal! Perlu penyesuaian.")

                # Hitung dan tampilkan interval asli
                nilai_list = list(input_nilai.values())
                nilai_list.sort(reverse=True)
                st.write(
                    f"Interval asli tertinggi-terendah: {format_nilai(nilai_list[0] - nilai_list[-1])}")

                # Lakukan penyesuaian
                adjusted_nilai, rule_applied = solve_interval(
                    input_nilai, max_interval)

                # Tampilkan aturan yang digunakan
                st.info(f"Aturan yang diterapkan: {rule_applied}")

                # Tampilkan tabel perbandingan nilai
                comparison = pd.DataFrame({
                    "Hakim": list(input_nilai.keys()),
                    "Nilai Asli": [format_nilai(input_nilai[hakim]) for hakim in input_nilai.keys()],
                    "Nilai Disesuaikan": [format_nilai(adjusted_nilai[hakim]) for hakim in adjusted_nilai.keys()]
                })
                st.table(comparison)

                # Hitung dan tampilkan interval baru
                adjusted_list = list(adjusted_nilai.values())
                adjusted_list.sort(reverse=True)
                st.write(
                    f"Interval baru tertinggi-terendah: {format_nilai(adjusted_list[0] - adjusted_list[-1])}")

        else:
            st.error("Harap masukkan nilai untuk semua hakim!")


if __name__ == '__main__':
    main()
