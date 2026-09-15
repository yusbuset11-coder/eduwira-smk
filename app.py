import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="EDUWIRA SMK - Ekosistem Digital Kewirausahaan",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Koneksi Google Sheets API (Multi-Tenant per Sekolah) ---
@st.cache_resource
def init_gspread():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Mengambil secret dari Streamlit Cloud secrets.toml
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

client = init_gspread()

# --- DATABASE / DAFTAR SEKOLAH ---
# Dictionary mapping Nama Sekolah ke Spreadsheet ID masing-masing
SEKOLAH_SPREADSHEET = {
    "SMK Negeri 1 Kwanyar": "17BPw0rugvLPp4P8SeWtfXPObrH2Fkb_IGVFXomyf4",
    "SMK Negeri 2 Bangkalan": "1ETKhDfk2b23y8FscypR43-mrrtT2vlQ38w8BqFUWY",
    # Tambahkan sekolah 3 s.d. 10 di sini jika sudah ada
}

# --- FUNGSI HELPER GOOGLE SHEETS ---
def get_school_records(spreadsheet_id, sheet_name):
    """Mengambil seluruh data dari sheet tertentu di spreadsheet sekolah."""
    if not client:
        return pd.DataFrame()
    try:
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

def append_school_record(spreadsheet_id, sheet_name, row_dict):
    """Menambahkan baris baru ke sheet Google Spreadsheet sekolah."""
    if not client:
        return False, "Koneksi Google Sheets gagal."
    try:
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        # Urutan kolom disesuaikan dengan keys dictionary
        row_values = list(row_dict.values())
        worksheet.append_row(row_values)
        return True, ""
    except Exception as e:
        return False, str(e)

# --- INISIALISASI SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "unit_sekolah" not in st.session_state:
    st.session_state.unit_sekolah = list(SEKOLAH_SPREADSHEET.keys())[0]
if "last_trx" not in st.session_state:
    st.session_state.last_trx = None

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>⚡ EDUWIRA SMK</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Ekosistem Digital Untuk Kewirausahaan Sekolah Menengah Kejuruan</h4>", unsafe_allow_html=True)
    st.write("")
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("login_form"):
            st.markdown("### 🔐 Login Akses Sistem")
            username_input = st.text_input("Username / Nama Pengguna")
            password_input = st.text_input("Password", type="password")
            role_pilih = st.selectbox("Pilih Hak Akses (Role)", ["Sekolah", "Admin Cabdin / Pusat"])
            
            # Jika role adalah Sekolah, munculkan pilihan unit sekolah
            unit_pilih = None
            if role_pilih == "Sekolah":
                unit_pilih = st.selectbox("Pilih Unit Sekolah", list(SEKOLAH_SPREADSHEET.keys()))
                
            submit_login = st.form_submit_button("Masuk Aplikasi", use_container_width=True)
            
            if submit_login:
                if username_input.strip() != "":
                    st.session_state.logged_in = True
                    st.session_state.username = username_input
                    st.session_state.role = role_pilih
                    if unit_pilih:
                        st.session_state.unit_sekolah = unit_pilih
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("⚠️ Username tidak boleh kosong!")
    st.stop()

# --- SIDEBAR NAVIGASI & INFO ---
with st.sidebar:
    st.markdown(f"👤 **Admin:** {st.session_state.username}")
    if st.session_state.role == "Sekolah":
        st.markdown(f"🏢 **Unit:** {st.session_state.unit_sekolah}")
    st.markdown(f"🛡️ **Role:** {st.session_state.role}")
    st.markdown("---")
    
    st.markdown("### 🧭 Menu Navigasi")
    menu = st.radio(
        "Pilih Menu",
        [
            "Dashboard Utama",
            "Katalog Produk (TeFa)",
            "Catat Transaksi / Kasir",
            "Laporan & Analitik"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🚪 Keluar / Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.last_trx = None
        st.rerun()

# --- TENTUKAN SPREADSHEET AKTIF ---
nama_sekolah_kini = st.session_state.unit_sekolah
active_spreadsheet_id = SEKOLAH_SPREADSHEET.get(nama_sekolah_kini, list(SEKOLAH_SPREADSHEET.values())[0])

# ==========================================
# 1. MENU: DASHBOARD UTAMA
# ==========================================
if menu == "Dashboard Utama":
    st.markdown(f"# EDUWIRA SMK")
    st.markdown("#### Ekosistem Digital Untuk Kewirausahaan Sekolah Menengah Kejuruan")
    st.markdown("*Pengembang Aplikasi: Yustinus Budi Setyanta - Pengawas SMK Cabdin Bangkalan*")
    st.markdown("---")
    
    st.markdown(f"### Dashboard Utama - {nama_sekolah_kini}")
    st.info("Gunakan menu di samping untuk mengelola katalog produk siswa, mencatat transaksi, dan memantau omzet penjualan pada Google Spreadsheet mandiri Anda.")
    
    # Ambil data dari MASTER_PRODUK & TRANSAKSI
    df_master_dash = get_school_records(active_spreadsheet_id, "MASTER_PRODUK")
    df_trx_dash = get_school_records(active_spreadsheet_id, "TRANSAKSI")
    
    total_produk = len(df_master_dash) if not df_master_dash.empty else 0
    total_omzet = 0
    total_trx_count = 0
    
    if not df_trx_dash.empty:
        total_trx_count = len(df_trx_dash)
        if "Total_Harga" in df_trx_dash.columns:
            total_omzet = pd.to_numeric(df_trx_dash["Total_Harga"], errors='coerce').sum()
        elif "total_harga" in df_trx_dash.columns:
            total_omzet = pd.to_numeric(df_trx_dash["total_harga"], errors='coerce').sum()

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(label="Total Produk Terdaftar", value=f"{total_produk} Produk", delta="Aktif")
    with col_m2:
        st.metric(label="Total Omzet Penjualan", value=f"Rp {total_omzet:,.0f}", delta=f"{total_trx_count} Transaksi")
    with col_m3:
        st.metric(label="Sumber Data", value="Google Sheets", delta="Terkoneksi")

# ==========================================
# 2. MENU: KATALOG PRODUK (TEFA)
# ==========================================
elif menu == "Katalog Produk (TeFa)":
    st.markdown("### 📦 Manajemen Katalog Produk Siswa")
    st.markdown(f"Kelola daftar produk Teaching Factory untuk unit **{nama_sekolah_kini}** langsung melalui sheet `MASTER_PRODUK` di Google Spreadsheet Anda.")
    
    tab1, tab2 = st.tabs(["📋 Daftar Produk", "➕ Tambah Produk Baru"])
    
    with tab1:
        st.markdown("### 📋 Daftar Produk Sekolah Anda")
        df_master = get_school_records(active_spreadsheet_id, "MASTER_PRODUK")
        
        if not df_master.empty:
            st.dataframe(df_master, use_container_width=True)
            st.success(f"✨ Menampilkan {len(df_master)} produk dari Google Spreadsheet.")
        else:
            st.warning("⚠️ Belum ada data produk di sheet `MASTER_PRODUK`. Silakan isi melalui tab sebelah atau langsung di Google Spreadsheet Anda.")
            
    with tab2:
        st.markdown("### ➕ Form Input Produk Baru ke Master Spreadsheet")
        with st.form("form_tambah_master_prod", clear_on_submit=True):
            kategori = st.selectbox("Kategori", ["Makanan & Minuman", "Kerajinan/Kriya", "Jasa & Layanan", "Teknologi & Elektronik", "Lainnya"])
            nama_produk = st.text_input("Nama Produk")
            harga = st.number_input("Harga (Rp)", min_value=0, step=500)
            jumlah_stok = st.number_input("Jumlah Stok", min_value=0, step=1)
            deskripsi = st.text_area("Deskripsi Produk")
            
            submit_master = st.form_submit_button("💾 Simpan Produk ke MASTER_PRODUK")
            
            if submit_master:
                if not nama_produk or not nama_produk.strip():
                    st.error("❌ Nama produk tidak boleh kosong!")
                elif harga <= 0:
                    st.error("❌ Harga produk harus lebih besar dari 0!")
                else:
                    new_row = {
                        "Kategori": kategori,
                        "Nama_Produk": nama_produk,
                        "Harga": harga,
                        "Jumlah_Stok": jumlah_stok,
                        "Deskripsi_Produk": deskripsi
                    }
                    success, err_msg = append_school_record(active_spreadsheet_id, "MASTER_PRODUK", new_row)
                    if success:
                        st.success(f"🎉 Produk '{nama_produk}' berhasil ditambahkan ke Google Spreadsheet!")
                        st.rerun()
                    else:
                        st.error(f"❌ Gagal menyimpan ke Google Spreadsheet. Detail Error: {err_msg}")

# ==========================================
# 3. MENU: CATAT TRANSAKSI / KASIR
# ==========================================
elif menu == "Catat Transaksi / Kasir":
    st.markdown("### 💰 Pencatatan Transaksi & Cetak Struk")
    st.write("Fitur kasir digital untuk mencatat penjualan produk dari `MASTER_PRODUK` ke sheet `TRANSAKSI`.")

    df_p = get_school_records(active_spreadsheet_id, "MASTER_PRODUK")

    if df_p.empty:
        st.warning("⚠️ Belum ada produk di `MASTER_PRODUK`. Tambahkan produk terlebih dahulu di menu Katalog Produk.")
    else:
        # Normalisasi nama kolom agar aman
        df_p.columns = df_p.columns.str.strip()
        col_nama = next((c for c in df_p.columns if "nama" in c.lower()), df_p.columns[1])
        col_harga = next((c for c in df_p.columns if "harga" in c.lower()), "Harga")
        col_stok = next((c for c in df_p.columns if "stok" in c.lower()), "Jumlah_Stok")

        list_produk = df_p[col_nama].dropna().tolist()
        
        selected_prod_name = st.selectbox("Pilih Produk", list_produk)
        
        # Ambil detail produk terpilih
        prod_row = df_p[df_p[col_nama] == selected_prod_name].iloc[0]
        harga_satuan = float(prod_row.get(col_harga, 0))
        stok_tersedia = int(prod_row.get(col_stok, 0))

        st.info(f"🏷️ Harga Satuan: Rp {harga_satuan:,.0f}  |  📦 Stok Tersedia: {stok_tersedia}")

        with st.form("form_kasir"):
            jumlah_beli = st.number_input("Jumlah Terjual (Unit)", min_value=1, max_value=max(1, stok_tersedia), step=1)
            pembeli = st.text_input("Nama Pembeli / Keterangan Pembeli (Opsional)", value="Umum")
            
            submit_trx = st.form_submit_button("🛒 Proses & Simpan Transaksi")

            if submit_trx:
                total_bayar = harga_satuan * jumlah_beli
                id_trx = str(uuid.uuid4())[:8].upper()
                waktu_trx = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                trx_row = {
                    "ID_Transaksi": id_trx,
                    "Tanggal": waktu_trx,
                    "Sekolah": nama_sekolah_kini,
                    "Nama_Produk": selected_prod_name,
                    "Jumlah_Terjual": jumlah_beli,
                    "Total_Harga": total_bayar,
                    "Pembeli": pembeli
                }
                
                # Simpan ke Google Sheets TRANSAKSI
                success, err = append_school_record(active_spreadsheet_id, "TRANSAKSI", trx_row)
                
                if success:
                    st.session_state.last_trx = {
                        "id_trx": id_trx,
                        "waktu": waktu_trx,
                        "kasir": st.session_state.username,
                        "produk": selected_prod_name,
                        "harga_satuan": harga_satuan,
                        "jumlah": jumlah_beli,
                        "total": total_bayar,
                        "pembeli": pembeli
                    }
                    st.success("🎉 Transaksi berhasil dicatat dan disinkronkan ke Google Spreadsheet!")
                    st.rerun()
                else:
                    st.error(f"❌ Gagal mencatat transaksi ke Spreadsheet: {err}")

    # Tampilkan Struk jika ada transaksi terakhir di session state
    if st.session_state.last_trx:
        t = st.session_state.last_trx
        st.markdown("---")
        struk_text = f"""
========================================
       STRUK PEMBELIAN / NOTA TeFa      
           {nama_sekolah_kini.upper()}       
========================================
ID Transaksi : {t['id_trx']}
Tanggal      : {t['waktu']}
Kasir / PJ   : {t['kasir']}
Pembeli      : {t['pembeli']}
----------------------------------------
Produk       : {t['produk']}
Harga Satuan : Rp {t['harga_satuan']:,.0f}
Jumlah Beli  : {t['jumlah']} unit
----------------------------------------
TOTAL BAYAR  : Rp {t['total']:,.0f}
========================================
 Terima kasih telah mendukung produk Vokasi!
========================================
"""
        st.markdown("### 📄 Pratinjau Struk Pembelian")
        st.code(struk_text, language="text")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Download Struk (TXT)",
                data=struk_text,
                file_name=f"Struk_{t['id_trx']}.txt",
                mime="text/plain",
            )

# ==========================================
# 4. MENU: LAPORAN & ANALITIK
# ==========================================
elif menu == "Laporan & Analitik":
    st.markdown("### 📊 Laporan & Analitik Penjualan")
    st.markdown(f"Rekapitulasi riwayat transaksi Teaching Factory unit **{nama_sekolah_kini}**.")
    
    df_trx_report = get_school_records(active_spreadsheet_id, "TRANSAKSI")
    
    if not df_trx_report.empty:
        st.dataframe(df_trx_report, use_container_width=True)
        
        # Hitung ringkasan
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            total_trx_item = len(df_trx_report)
            st.metric("Total Struk Transaksi", f"{total_trx_item} Transaksi")
        with col_r2:
            col_tot_name = next((c for c in df_trx_report.columns if "total" in c.lower()), df_trx_report.columns[-2])
            sum_omzet = pd.to_numeric(df_trx_report[col_tot_name], errors='coerce').sum()
            st.metric("Akumulasi Omzet", f"Rp {sum_omzet:,.0f}")
            
        # Tombol Download CSV Laporan
        csv_data = df_trx_report.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Laporan Transaksi (CSV)",
            data=csv_data,
            file_name=f"Laporan_Transaksi_{nama_sekolah_kini.replace(' ', '_')}.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ Belum ada data transaksi tercatat pada sheet `TRANSAKSI` di Google Spreadsheet sekolah ini.")
