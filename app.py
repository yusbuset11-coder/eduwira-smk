from datetime import datetime
import uuid
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st
from supabase import create_client

# --- INISIALISASI KONEKSI SUPABASE ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    supabase = None

# --- KONFIGURASI GOOGLE SHEETS (GSPREAD) ---
def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client

def get_school_records(spreadsheet_id, sheet_name):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

def append_school_record(spreadsheet_id, sheet_name, row_dict):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        headers = [h.strip() for h in worksheet.row_values(1)]
        
        # Jika sheet masih kosong (belum ada header), buat header otomatis
        if not headers or headers == ['']:
            headers = list(row_dict.keys())
            worksheet.append_row(headers)
        
        # Susun data berdasarkan urutan header di spreadsheet
        row_values = []
        for h in headers:
            matched_key = next((k for k in row_dict.keys() if k.lower() == h.lower()), None)
            row_values.append(row_dict.get(matched_key, "") if matched_key else "")
            
        worksheet.append_row(row_values)
        return True, "Sukses"
    except Exception as e:
        return False, str(e)

def update_school_stock(spreadsheet_id, sheet_name, prod_id_val, new_stock):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        cell = worksheet.find(str(prod_id_val))
        if cell:
            headers = [h.lower() for h in worksheet.row_values(1)]
            if "stok" in headers:
                stok_idx = headers.index("stok") + 1
                worksheet.update_cell(cell.row, stok_idx, new_stock)
                return True
        return False
    except Exception:
        return False

# --- KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="EDUWIRA SMK - Ekosistem Digital Vokasi",
    page_icon="🚀",
    layout="wide",
)

LOGO_URL = "https://lh3.googleusercontent.com/d/1a-b-_KKjgSyN7RnvvKn85_P-hektUarE"

# --- INISIALISASI SESSION STATE GLOBAL ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "admin_nama" not in st.session_state:
    st.session_state.admin_nama = ""
if "nama_sekolah" not in st.session_state:
    st.session_state.nama_sekolah = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "spreadsheet_id" not in st.session_state:
    st.session_state.spreadsheet_id = ""
if "last_trx" not in st.session_state:
    st.session_state.last_trx = None

# --- STYLING CSS KUSTOM ---
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 4rem;
            max-width: 1250px !important;
        }
        .stApp {
            background-color: #0b0f19;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #f3f4f6;
        }
        .stTextInput input {
            background-color: #111827 !important;
            color: #ffffff !important;
            border: 1px solid #374151 !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            font-size: 16px !important;
        }
        .stButton > button {
            width: 100%;
            border-radius: 10px;
            font-weight: 700;
            font-size: 17px !important;
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
            color: white;
            border: none;
            padding: 0.75rem 1rem;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- BANNER UTAMA ---
st.markdown(
    f"""
    <div style="background: linear-gradient(180deg, #111827 0%, #0d1322 100%); border: 1px solid #1f2937; border-radius: 16px; padding: 40px 24px; margin: 0 auto 24px auto; width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 16px; width: 100%;">
            <img src="{LOGO_URL}" style="height: 72px; width: auto; object-fit: contain; border-radius: 8px; display: block;" alt="Logo EDUWIRA SMK">
        </div>
        <div style="color: #ffffff; font-size: 48px; font-weight: 800; margin-bottom: 12px; letter-spacing: 1px; line-height: 1.1; width: 100%;">EDUWIRA SMK</div>
        <div style="color: #93c5fd; font-size: 28px; font-weight: 700; margin-bottom: 10px; letter-spacing: 0.5px; line-height: 1.3; width: 100%;">Ekosistem Digital Untuk Kewirausahaan Sekolah Menengah Kejuruan</div>
        <div style="color: #facc15; font-size: 18px; font-weight: 600; letter-spacing: 0.5px; width: 100%;">Pengembang Aplikasi: Yustinus Budi Setyanta - Pengawas SMK Cabdin Bangkalan</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- KONDISI 1: BELUM LOGIN ---
if not st.session_state.logged_in:
    st.markdown(
        '<div style="background: #111827; padding: 28px 32px; border-radius: 16px; border: 1px solid #1f2937; width: 100%; margin: 0 auto 20px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center;"><div style="color: #818cf8; font-size: 20px; font-weight: 700; margin-bottom: 8px;">🔐 Login Portal EDUWIRA</div><div style="color: #e2e8f0; font-size: 16px; font-weight: 500;">Silakan masukkan <b>Token</b> atau <b>Email</b> Anda untuk mengakses ekosistem.</div></div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        with st.form("form_login_supabase"):
            input_user = st.text_input(
                "Token / Email",
                placeholder="Contoh: yustinus-budi@gmail.com atau EduwiraSMK-01",
            )
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            btn_masuk = st.form_submit_button("🚀 Masuk Ekosistem", use_container_width=True)

            if btn_masuk:
                if not input_user:
                    st.warning("⚠️ Mohon masukkan Token atau Email terlebih dahulu.")
                elif supabase is None:
                    st.error("❌ Koneksi Supabase belum terinisialisasi.")
                else:
                    with st.spinner("Memverifikasi data dari Supabase..."):
                        try:
                            response = supabase.table("master_registry").select("*").execute()
                            data_registry = response.data
                        except Exception as e:
                            data_registry = []
                            st.error(f"Gagal terhubung ke Supabase: {e}")

                    if data_registry:
                        df_reg = pd.DataFrame(data_registry)
                        df_reg.columns = df_reg.columns.str.strip()

                        token_col = "token" if "token" in df_reg.columns else df_reg.columns[0]
                        email_col = "email" if "email" in df_reg.columns else df_reg.columns[1]
                        admin_col = "admin_nama" if "admin_nama" in df_reg.columns else df_reg.columns[2]
                        sekolah_col = "nama_sekolah" if "nama_sekolah" in df_reg.columns else df_reg.columns[1]
                        role_col = "role" if "role" in df_reg.columns else None
                        sheet_col = "spreadsheet_id" if "spreadsheet_id" in df_reg.columns else None

                        matched = df_reg[
                            (df_reg[token_col].astype(str).str.strip().str.lower() == input_user.strip().lower()) |
                            (df_reg[email_col].astype(str).str.strip().str.lower() == input_user.strip().lower())
                        ]

                        if not matched.empty:
                            row = matched.iloc[0]
                            st.session_state.logged_in = True
                            st.session_state.admin_nama = str(row.get(admin_col, "Administrator"))
                            st.session_state.nama_sekolah = str(row.get(sekolah_col, "Pusat Pengawas"))
                            st.session_state.spreadsheet_id = str(row.get(sheet_col, "")) if sheet_col else ""
                            
                            r_val = str(row.get(role_col, "")).strip().lower() if role_col else ""
                            if not r_val:
                                if "dinas" in input_user.lower() or "yustinus" in st.session_state.admin_nama.lower():
                                    st.session_state.role = "Pengawas"
                                else:
                                    st.session_state.role = "Sekolah"
                            else:
                                st.session_state.role = r_val.capitalize()

                            st.success(f"🎉 Berhasil masuk! Selamat datang, {st.session_state.admin_nama} ({st.session_state.nama_sekolah}).")
                            st.rerun()
                        else:
                            st.error("❌ Token atau Email tidak ditemukan di `master_registry`.")
                    else:
                        st.error("❌ Tabel `master_registry` kosong.")

# --- KONDISI 2: SUDAH LOGIN ---
else:
    # --- SIDEBAR INFORMASI AKUN & NAVIGASI ---
    st.sidebar.markdown(f"👤 **Admin:** {st.session_state.admin_nama}")

# Jika rolenya Pengawas, tampilkan "Cabdin (Pengawas)", jika bukan tampilkan nama sekolah aslinya
    unit_tampil = (
        "Cabdin (Pengawas)"
        if st.session_state.role.lower() == "pengawas"
        else st.session_state.nama_sekolah
    )
    st.sidebar.markdown(f"🏫 **Unit:** {unit_tampil}")

    st.sidebar.markdown(f"🛡️ **Role:** `{st.session_state.role}`")
    st.sidebar.divider()

    st.sidebar.markdown("### 🧭 Menu Navigasi")

    is_pengawas = st.session_state.role.lower() == "pengawas" or "dinas" in st.session_state.admin_nama.lower() or "dinas" in st.session_state.nama_sekolah.lower()

    if is_pengawas:
        menu = st.sidebar.radio(
            "Pilih Menu",
            [
                "📊 Dashboard Rekap PS",
                "🏫 Daftar SMK Binaan",
            ],
        )
    else:
        menu = st.sidebar.radio(
            "Pilih Menu",
            [
                "🏠 Dashboard Utama",
                "📦 Katalog Produk (TeFa)",
                "💰 Catat Transaksi / Kasir",
                "📊 Laporan & Analitik",
            ],
        )

    st.sidebar.divider()
    if st.sidebar.button("🚪 Keluar / Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.admin_nama = ""
        st.session_state.nama_sekolah = ""
        st.session_state.role = ""
        st.session_state.spreadsheet_id = ""
        st.session_state.last_trx = None
        st.rerun()

    # ==========================================
    # LOGIC KELOMPOK 1: MENU PENGAWAS (MONITORING LINTAS SPREADSHEET)
    # ==========================================
    if is_pengawas:
        if menu == "📊 Dashboard Rekap PS":
            st.markdown("### 📊 Dashboard Rekapitulasi Kewirausahaan SMK Se-Binaan")
            st.write("Memantau rekapitulasi produk dan transaksi langsung dari Google Spreadsheet masing-masing sekolah.")

            try:
                res_reg = supabase.table("master_registry").select("*").execute()
                df_reg = pd.DataFrame(res_reg.data) if res_reg.data else pd.DataFrame()
            except Exception as e:
                st.error(f"Gagal mengambil data registry dari Supabase: {e}")
                df_reg = pd.DataFrame()

            if not df_reg.empty:
                role_col = "role" if "role" in df_reg.columns else None
                if role_col:
                    df_sekolah = df_reg[df_reg[role_col].astype(str).str.strip().str.lower() != "pengawas"]
                else:
                    df_sekolah = df_reg

                all_summary = []
                total_omzet_all = 0
                total_prod_all = 0
                total_trx_all = 0

                sekolah_col_name = "nama_sekolah" if "nama_sekolah" in df_reg.columns else df_reg.columns[1]
                admin_col_name = "admin_nama" if "admin_nama" in df_reg.columns else df_reg.columns[2]
                sheet_id_col = "spreadsheet_id" if "spreadsheet_id" in df_reg.columns else None

                for _, row in df_sekolah.iterrows():
                    sch_name = str(row.get(sekolah_col_name, "Sekolah"))
                    admin_pj = str(row.get(admin_col_name, "-"))
                    sch_sheet_id = str(row.get(sheet_id_col, "")) if sheet_id_col else ""

                    prod_count = 0
                    omzet_sekolah = 0
                    trx_count = 0

                    if sch_sheet_id:
                        # Tarik data dari Google Spreadsheet masing-masing sekolah
                        df_p_sch = get_school_records(sch_sheet_id, "PRODUK_SMK")
                        df_t_sch = get_school_records(sch_sheet_id, "TRANSAKSI")

                        prod_count = len(df_p_sch)
                        trx_count = len(df_t_sch)

                        omzet_col = "total_harga" if "total_harga" in df_t_sch.columns else ("Total_Harga" if "Total_Harga" in df_t_sch.columns else None)
                        if omzet_col and not df_t_sch.empty:
                            omzet_sekolah = pd.to_numeric(df_t_sch[omzet_col], errors='coerce').sum()

                    total_omzet_all += omzet_sekolah
                    total_prod_all += prod_count
                    total_trx_all += trx_count

                    all_summary.append({
                        "Nama Sekolah": sch_name,
                        "Admin PJ": admin_pj,
                        "Total Produk": prod_count,
                        "Total Transaksi": trx_count,
                        "Total Omzet (Rp)": omzet_sekolah,
                    })

                df_summary = pd.DataFrame(all_summary)

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Akumulasi Omzet Cabdin", f"Rp {total_omzet_all:,.0f}", delta="Semua Sekolah Binaan")
                with c2:
                    st.metric("Total Produk TeFa Terdaftar", f"{total_prod_all} Produk")
                with c3:
                    st.metric("Total Transaksi Keseluruhan", f"{total_trx_all} Transaksi")

                st.markdown("---")
                st.markdown("#### 📋 Tabel Performa Kewirausahaan per SMK Binaan")
                if not df_summary.empty:
                    df_summary = df_summary.reset_index(drop=True)
                    df_summary.index = range(1, len(df_summary) + 1)
                    st.dataframe(df_summary, use_container_width=True)
                else:
                    st.info("Belum ada data rekapitulasi sekolah.")
            else:
                st.warning("Tabel `master_registry` kosong di Supabase.")

        elif menu == "🏫 Daftar SMK Binaan":
            st.markdown("### 🏫 Daftar Master Registry SMK Binaan (Supabase)")
            st.write("Daftar akun sekolah binaan beserta Spreadsheet ID masing-masing.")

            try:
                res = supabase.table("master_registry").select("*").execute()
                df_reg = pd.DataFrame(res.data) if res.data else pd.DataFrame()
            except Exception:
                df_reg = pd.DataFrame()

            if not df_reg.empty:
                df_reg = df_reg.reset_index(drop=True)
                df_reg.index = range(1, len(df_reg) + 1)
                st.dataframe(df_reg, use_container_width=True)
            else:
                st.info("Data registry belum tersedia.")

    # ==========================================
    # LOGIC KELOMPOK 2: MENU SEKOLAH MANDIRI (GOOGLE SHEETS MASING-MASING)
    # ==========================================
    else:
        nama_sekolah_kini = st.session_state.nama_sekolah
        active_spreadsheet_id = st.session_state.spreadsheet_id

        if not active_spreadsheet_id:
            st.error("❌ `spreadsheet_id` belum diatur untuk sekolah ini di tabel `master_registry` Supabase. Hubungi Pengawas.")
        else:
            if menu == "🏠 Dashboard Utama":
                st.markdown(f'<div style="color: #f3f4f6; font-size: 20px; font-weight: 700; margin-bottom: 10px;">Dashboard Utama - {nama_sekolah_kini}</div>', unsafe_allow_html=True)
                st.info("Gunakan menu di samping untuk mengelola katalog produk siswa, mencatat transaksi, dan memantau omzet penjualan pada Google Spreadsheet mandiri Anda.")

                df_p = get_school_records(active_spreadsheet_id, "PRODUK_SMK")
                df_t = get_school_records(active_spreadsheet_id, "TRANSAKSI")

                total_prod = len(df_p)
                total_trx_count = len(df_t)
                omzet_col = "total_harga" if "total_harga" in df_t.columns else ("Total_Harga" if "Total_Harga" in df_t.columns else None)
                total_omzet = pd.to_numeric(df_t[omzet_col], errors='coerce').sum() if (not df_t.empty and omzet_col) else 0

                # Berikan bobot lebih besar pada kolom ketiga (misal: [1, 1, 1.4])
                col_a, col_b, col_c = st.columns([1, 1, 1.4])
                with col_a:
                    st.metric(label="Total Produk Terdaftar", value=f"{total_prod} Produk", delta="Aktif")
                with col_b:
                    st.metric(label="Total Omzet Penjualan", value=f"Rp {total_omzet:,.0f}", delta=f"{total_trx_count} Transaksi")
                with col_c:
                    st.metric(label="Sumber Data", value="Google Sheets", delta="Terkoneksi")

            elif menu == "📦 Katalog Produk (TeFa)":
                st.markdown("### 📦 Manajemen Katalog Produk Siswa")
                st.write(f"Kelola daftar produk Teaching Factory untuk unit **{nama_sekolah_kini}** pada Google Spreadsheet Anda.")

                tab1, tab2 = st.tabs(["📋 Daftar Produk", "➕ Tambah Produk Baru"])

                with tab1:
                    st.markdown("#### Daftar Produk Sekolah Anda")
                    df_p = get_school_records(active_spreadsheet_id, "PRODUK_SMK")

                    if not df_p.empty:
                        df_p = df_p.reset_index(drop=True)
                        df_p.index = range(1, len(df_p) + 1)
                        st.dataframe(df_p, use_container_width=True)
                    else:
                        st.info("ℹ️ Belum ada produk terdaftar di Google Spreadsheet sekolah Anda (atau sheet 'PRODUK_SMK' belum dibuat/kosong).")

                with tab2:
                    st.markdown("### ➕ Form Input Produk Baru")
                    with st.form("form_tambah_produk_gs", clear_on_submit=True):
                        nama_produk = st.text_input("Nama Produk")
                        kategori = st.selectbox(
                            "Kategori",
                            [
                                "Makanan & Minuman",
                                "Kerajinan / Kriya",
                                "Jasa & Layanan",
                                "Teknologi / Elektronik",
                                "Lainnya",
                            ],
                        )
                        harga = st.number_input("Harga (Rp)", min_value=0, step=500)
                        stok = st.number_input("Jumlah Stok", min_value=0, step=1)
                        deskripsi = st.text_area("Deskripsi Produk")
                        
                        submit_prod = st.form_submit_button("📦 Simpan Produk ke Google Spreadsheet")
                        
                        if submit_prod:
                            if not nama_produk or not nama_produk.strip():
                                st.error("❌ Nama produk tidak boleh kosong!")
                            elif harga <= 0:
                                st.error("❌ Harga produk harus lebih besar dari 0!")
                            else:
                                id_prod = str(uuid.uuid4())[:8]
                                new_row = {
                                    "id_produk": id_prod,
                                    "sekolah": nama_sekolah_kini,
                                    "nama_produk": nama_produk,
                                    "kategori": kategori,
                                    "harga": harga,
                                    "stok": stok,
                                    "deskripsi_produk": deskripsi,
                                }
                                success, err_msg = append_school_record(active_spreadsheet_id, "PRODUK_SMK", new_row)
                                if success:
                                    st.success(f"🎉 Produk '{nama_produk}' berhasil disimpan ke Google Spreadsheet Anda!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Gagal menyimpan ke Google Spreadsheet. Detail Error: {err_msg}")

            elif menu == "💰 Catat Transaksi / Kasir":
                st.markdown("### 💰 Pencatatan Transaksi & Cetak Struk")
                st.write("Fitur kasir digital untuk mencatat penjualan dan menyimpannya langsung ke Google Spreadsheet Anda.")

                df_p = get_school_records(active_spreadsheet_id, "PRODUK_SMK")

                if st.session_state.last_trx:
                    t = st.session_state.last_trx
                    st.success("🎉 Transaksi berhasil dicatat dan disinkronkan ke Google Spreadsheet!")

                    struk_text = f"""
========================================
       STRUK PEMBELIAN / NOTA TeFa      
           {nama_sekolah_kini.upper()}       
========================================
ID Transaksi : {t['id_trx']}
Tanggal      : {t['waktu']}
Kasir / PJ   : {t['kasir']}
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
                    st.markdown("### 🧾 Pratinjau Struk Pembelian")
                    st.code(struk_text, language="text")

                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.download_button(
                            label="📥 Download Struk (TXT)",
                            data=struk_text,
                            file_name=f"Struk_{t['id_trx']}.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )
                    with col_d2:
                        if st.button("🔄 Catat Transaksi Baru", use_container_width=True):
                            st.session_state.last_trx = None
                            st.rerun()

                    st.markdown("---")

                if not st.session_state.last_trx:
                    if not df_p.empty:
                        name_key = "nama_produk" if "nama_produk" in df_p.columns else ("Nama_Produk" if "Nama_Produk" in df_p.columns else df_p.columns[2])
                        list_produk = df_p[name_key].tolist()
                        pilih_produk = st.selectbox("Pilih Produk", list_produk)

                        selected_row = df_p[df_p[name_key] == pilih_produk].iloc[0]
                        # Mencari kolom secara otomatis tanpa peduli huruf besar/kecil
                        price_key = next((c for c in df_p.columns if c.lower() == "harga"), "Harga")
                        stock_key = next((c for c in df_p.columns if c.lower() == "stok"), "Stok")

                        harga_satuan = float(selected_row.get(price_key, 0))
                        stok_tersedia = int(selected_row.get(stock_key, 0))

                        st.info(f"💵 Harga Satuan: Rp {harga_satuan:,.0f} | 📦 Stok Tersedia: {stok_tersedia}")

                        with st.form("form_transaksi_gs"):
                            jumlah_beli = st.number_input(
                                "Jumlah Terjual",
                                min_value=1,
                                max_value=max(1, stok_tersedia),
                                step=1,
                            )
                            total_harga = harga_satuan * jumlah_beli
                            st.markdown(f"**Total Harga: Rp {total_harga:,.0f}**")

                            submit_trx = st.form_submit_button("🛒 Proses Transaksi & Simpan")

                            if submit_trx:
                                id_trx = str(uuid.uuid4())[:8].upper()
                                waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                new_trx_row = {
                                    "id_transaksi": id_trx,
                                    "tanggal": waktu_sekarang,
                                    "sekolah": nama_sekolah_kini,
                                    "nama_produk": pilih_produk,
                                    "jumlah_terjual": int(jumlah_beli),
                                    "total_harga": float(total_harga),
                                }
                                
                                # Append transaksi ke sheet TRANSAKSI
                                succ_trx = append_school_record(active_spreadsheet_id, "TRANSAKSI", new_trx_row)
                                
                                # Update stok di sheet PRODUK_SMK
                                prod_id_key = "id_produk" if "id_produk" in selected_row else selected_row.index[0]
                                prod_id_val = selected_row[prod_id_key]
                                new_stock = max(0, stok_tersedia - int(jumlah_beli))
                                update_school_stock(active_spreadsheet_id, "PRODUK_SMK", prod_id_val, new_stock)

                                if succ_trx:
                                    st.session_state.last_trx = {
                                        "id_trx": id_trx,
                                        "waktu": waktu_sekarang,
                                        "produk": pilih_produk,
                                        "harga_satuan": harga_satuan,
                                        "jumlah": jumlah_beli,
                                        "total": total_harga,
                                        "kasir": st.session_state.admin_nama,
                                    }
                                    st.rerun()
                                else:
                                    st.error("❌ Gagal mencatat transaksi ke Google Spreadsheet. Pastikan sheet bernama `TRANSAKSI` tersedia.")
                    else:
                        st.warning("⚠️ Belum ada data produk di Google Spreadsheet sekolah Anda. Tambahkan produk terlebih dahulu di menu **Katalog Produk (TeFa)**.")

            elif menu == "📊 Laporan & Analitik":
                st.markdown("### 📊 Laporan & Analitik Penjualan")
                st.write(f"Analisis riwayat transaksi penjualan untuk unit **{nama_sekolah_kini}**.")

                df_t = get_school_records(active_spreadsheet_id, "TRANSAKSI")

                if not df_t.empty:
                    df_t = df_t.reset_index(drop=True)
                    df_t.index = range(1, len(df_t) + 1)
                    st.markdown("#### Riwayat Transaksi Penjualan")
                    st.dataframe(df_t, use_container_width=True)

                    omzet_col = "total_harga" if "total_harga" in df_t.columns else ("Total_Harga" if "Total_Harga" in df_t.columns else None)
                    qty_col = "jumlah_terjual" if "jumlah_terjual" in df_t.columns else ("Jumlah_Terjual" if "Jumlah_Terjual" in df_t.columns else None)

                    total_omzet_rep = pd.to_numeric(df_t[omzet_col], errors='coerce').sum() if omzet_col else 0
                    total_item_sold = pd.to_numeric(df_t[qty_col], errors='coerce').sum() if qty_col else len(df_t)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Omzet", f"Rp {total_omzet_rep:,.0f}")
                    with col2:
                        st.metric("Total Unit Terjual", f"{total_item_sold} Unit")
                else:
                    st.info("ℹ️ Belum ada data transaksi yang tercatat di Google Spreadsheet Anda (atau sheet 'TRANSAKSI' belum dibuat).")
