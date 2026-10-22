from flask import Flask, render_template_string, request, jsonify
import random
import time
import math
import os

app = Flask(__name__)
odalar = {}

def mesafe_hesapla(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def yon_hesapla(lat1, lon1, lat2, lon2):
    dl = math.radians(lon2 - lon1)
    p1, p2 = math.radians(lat1), math.radians(lat2)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    brng = (math.degrees(math.atan2(y, x)) + 360) % 360
    yonler = ["kuzeye", "kuzeydoğuya", "doğuya", "güneydoğuya", "güneye", "güneybatıya", "batıya", "kuzeybatıya"]
    return yonler[round(brng / 45) % 8]

def sure_formatla(saniye):
    saniye = max(0, int(saniye))
    return f"{saniye // 60:02d}:{saniye % 60:02d}"

HTML_KODU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    <title>HUSH</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; user-select: none; }
        body { margin: 0; padding: 0; background: #f5f5f3; color: #111; display: flex; justify-content: center; }
        .telefon { width: 100%; max-width: 430px; min-height: 100vh; background: #f5f5f3; position: relative; display: flex; flex-direction: column; overflow-x: hidden; }
        .ekran { display: none; flex-direction: column; flex: 1; padding: 18px; }
        .aktif { display: flex; }
        .kart { background: #fff; border-radius: 18px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.04); }
        .btn-siyah { background: #0f0f0f; color: #fff; border: none; border-radius: 16px; padding: 17px; font-size: 16px; font-weight: 700; width: 100%; cursor: pointer; margin-top: 8px; }
        .btn-beyaz { background: #fff; color: #111; border: 1px solid #e2e2e2; border-radius: 16px; padding: 17px; font-size: 16px; font-weight: 700; width: 100%; cursor: pointer; margin-top: 8px; }
        .satir { display: flex; justify-content: space-between; align-items: center; }
        .sayac-kutu { display: flex; align-items: center; gap: 12px; background: #f5f5f3; padding: 6px 12px; border-radius: 12px; }
        .sayac-btn { background: none; border: none; font-size: 20px; font-weight: bold; cursor: pointer; width: 28px; }
        .seg-grup { display: flex; background: #f5f5f3; border-radius: 12px; padding: 4px; gap: 4px; }
        .seg-btn { border: none; background: transparent; padding: 8px 14px; border-radius: 9px; font-weight: 600; cursor: pointer; color: #777; }
        .seg-btn.secili { background: #111; color: #fff; }
        .kod-kutu { width: 44px; height: 54px; background: #fff; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
        .badge-hazir { background: #e6f9ed; color: #15803d; padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }
        .badge-kapali { background: #fee2e2; color: #b91c1c; padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }
        
        #harita_secim, #oyun_harita { 
            width: 100%; 
            height: 330px; 
            border-radius: 22px; 
            z-index: 1; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            border: 2px solid #fff;
            background: #e5e7eb;
        }
        .leaflet-control-attribution { display: none !important; }
        
        .leaflet-marker-icon {
            transition: transform 0.6s cubic-bezier(0.25, 1, 0.5, 1);
        }

        .oyuncu-radar {
            position: relative;
            width: 22px;
            height: 22px;
        }
        .oyuncu-merkez {
            width: 16px;
            height: 16px;
            background: #0f0f0f;
            border: 3px solid #ffffff;
            border-radius: 50%;
            position: absolute;
            top: 3px;
            left: 3px;
            z-index: 2;
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        }
        .oyuncu-dalga {
            width: 22px;
            height: 22px;
            background: rgba(22, 163, 74, 0.45);
            border-radius: 50%;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
            animation: radarDalga 1.8s infinite ease-out;
        }
        @keyframes radarDalga {
            0% { transform: scale(0.8); opacity: 1; }
            100% { transform: scale(2.6); opacity: 0; }
        }

        .hedef-pin {
            position: relative;
            width: 24px;
            height: 24px;
        }
        .hedef-merkez {
            width: 18px;
            height: 18px;
            background: #ef4444;
            border: 3px solid #ffffff;
            border-radius: 50%;
            position: absolute;
            top: 3px;
            left: 3px;
            z-index: 2;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.6);
        }
        .hedef-dalga {
            width: 24px;
            height: 24px;
            background: rgba(239, 68, 68, 0.5);
            border-radius: 50%;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
            animation: radarDalga 1.4s infinite ease-out;
        }
        .hedef-etiket {
            position: absolute;
            top: -24px;
            left: 50%;
            transform: translateX(-50%);
            background: #991b1b;
            color: #fff;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 7px;
            border-radius: 8px;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .harita-odak-btn {
            position: absolute;
            bottom: 14px;
            right: 14px;
            width: 42px;
            height: 42px;
            background: #fff;
            border: none;
            border-radius: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 500;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .switch { position: relative; display: inline-block; width: 50px; height: 28px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .3s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 22px; width: 22px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%; }
        input:checked + .slider { background-color: #111; }
        input:checked + .slider:before { transform: translateX(22px); }
        
        #cep_modu_katman {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: #000000;
            color: #222222;
            z-index: 99999;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 20px;
        }

        .hizli-mesaj-bar {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding: 4px 0;
            margin-top: 6px;
            scrollbar-width: none;
        }
        .hizli-mesaj-bar::-webkit-scrollbar { display: none; }
        .hizli-chip {
            background: #eef2ff;
            color: #3730a3;
            border: 1px solid #c7d2fe;
            padding: 6px 12px;
            border-radius: 14px;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
            cursor: pointer;
        }
    </style>
</head>
<body onclick="ekranAcikTut(); sesHazirla();">

<div id="cep_modu_katman" onclick="cepModuTiklama()">
    <div style="font-size: 28px; margin-bottom: 10px;">🌙</div>
    <div style="font-weight: 800; font-size: 16px; color: #333;">CEP MODU AKTİF</div>
    <div style="font-size: 12px; color: #1a1a1a; margin-top: 6px;">GPS ve titreşim uyarıları arka planda çalışıyor.<br>Ekranı açmak için <b>iki kez dokun</b>.</div>
    <div id="cep_sayac_bilgi" style="font-size: 22px; font-weight: 900; color: #1f1f1f; margin-top: 25px;">--:--</div>
</div>

<div class="telefon">

    <!-- 1. EKRAN: ANA EKRAN -->
    <div id="ekran_home" class="ekran aktif">
        <div class="satir" style="margin-bottom: 18px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="background:#111; color:#fff; width:34px; height:34px; border-radius:9px; display:flex; align-items:center; justify-content:center; font-weight:bold;">◉</div>
                <span style="font-size:20px; font-weight:900; letter-spacing:1px;">HUSH</span>
            </div>
            <input type="text" id="oyuncu_ismi" placeholder="Adın (Örn: Mert Efe)" style="border:1px solid #ddd; border-radius:20px; padding:8px 14px; width:170px; font-weight:600; text-align:right;" onchange="localStorage.setItem('hush_isim', this.value)">
        </div>

        <p style="color:#666; margin:0;">İyi akşamlar,</p>
        <h1 style="font-size:32px; margin:4px 0 18px 0; font-weight:800;">Kaybolmaya<br>hazır mısın?</h1>

        <div class="kart satir" style="padding: 20px;">
            <div><div id="ana_xp" style="font-size:26px; font-weight:800;">4.820</div><div style="font-size:12px; color:#888;">Toplam XP</div></div>
            <div style="border-left:1px solid #eee; padding-left:20px;"><div style="font-size:26px; font-weight:800;">12</div><div style="font-size:12px; color:#888;">Galibiyet</div></div>
            <div style="border-left:1px solid #eee; padding-left:20px;"><div style="font-size:26px; font-weight:800;">31</div><div style="font-size:12px; color:#888;">Oyun</div></div>
        </div>

        <div class="kart satir">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="width:42px; height:42px; border-radius:50%; background:#dcfce7; border:2px dashed #16a34a;"></div>
                <div>
                    <div style="font-size:12px; color:#888;">GPS Durumu</div>
                    <div id="ana_gps_durum" style="font-weight:700; color:#15803d;">Otomatik Konum Hazır</div>
                </div>
            </div>
            <span style="color:#16a34a; font-weight:800;">AKTİF</span>
        </div>

        <button class="btn-siyah" onclick="gpsBaslat(); ekranGec('ekran_kur')">+  OYUN KUR</button>
        <div style="display:flex; gap:8px; margin-top:8px;">
            <input type="text" id="girilen_kod" placeholder="6 Haneli Oda Kodu" maxlength="6" style="flex:1; border-radius:16px; border:1px solid #ddd; padding:0 16px; font-size:16px; font-weight:700;">
            <button class="btn-beyaz" style="width:auto; margin:0; padding:16px 24px;" onclick="gpsBaslat(); odayaKatil()"># OYUNA KATIL</button>
        </div>

        <div class="kart satir" style="margin-top:auto; justify-content:space-around; padding:12px;">
            <div style="text-align:center; font-size:12px; font-weight:600;">👥<br>Arkadaşlar</div>
            <div style="text-align:center; font-size:12px; font-weight:600;">🏆<br>Sıralama</div>
            <div style="text-align:center; font-size:12px; font-weight:600;">👤<br>Profil</div>
        </div>
    </div>

    <!-- 2. EKRAN: OYUN KUR -->
    <div id="ekran_kur" class="ekran">
        <div class="satir" style="margin-bottom:15px;">
            <button onclick="ekranGec('ekran_home')" style="background:none; border:none; font-size:22px; cursor:pointer;">‹</button>
            <span style="font-weight:800; font-size:17px;">Oyun kur</span>
            <span style="width:22px;"></span>
        </div>

        <div class="kart" style="background:#111; color:#fff; display:flex; align-items:center; gap:14px;">
            <div style="font-size:24px;">👁</div>
            <div><div style="font-size:12px; color:#aaa;">Oyun modu</div><div style="font-size:17px; font-weight:700;">Klasik Saklambaç</div></div>
        </div>

        <div class="kart satir">
            <div><div style="font-weight:700;">Oyuncu sayısı</div><div style="font-size:12px; color:#888;">4 ile 20 arası</div></div>
            <div class="sayac-kutu">
                <button class="sayac-btn" onclick="sayiDegis('oyuncu', -1)">−</button>
                <span id="val_oyuncu" style="font-weight:800; min-width:20px; text-align:center;">8</span>
                <button class="sayac-btn" onclick="sayiDegis('oyuncu', 1)">+</button>
            </div>
        </div>

        <div class="kart satir">
            <div><div style="font-weight:700;">Oyun süresi</div><div style="font-size:12px; color:#888;">Dakika</div></div>
            <div class="seg-grup" id="grp_sure">
                <button class="seg-btn" onclick="segSec('sure', 10, this)">10</button>
                <button class="seg-btn secili" onclick="segSec('sure', 20, this)">20</button>
                <button class="seg-btn" onclick="segSec('sure', 30, this)">30</button>
            </div>
        </div>

        <div class="kart satir">
            <div><div style="font-weight:700;">Saklanma süresi</div><div style="font-size:12px; color:#888;">Husher'lar başlamadan</div></div>
            <div class="seg-grup" id="grp_saklanma">
                <button class="seg-btn secili" onclick="segSec('saklanma', 3, this)">3</button>
                <button class="seg-btn" onclick="segSec('saklanma', 5, this)">5</button>
            </div>
        </div>

        <div class="kart satir">
            <div><div style="font-weight:700;">Husher sayısı</div><div style="font-size:12px; color:#888;">Rastgele seçilir</div></div>
            <div class="sayac-kutu">
                <button class="sayac-btn" onclick="sayiDegis('husher', -1)">−</button>
                <span id="val_husher" style="font-weight:800; min-width:20px; text-align:center;">2</span>
                <button class="sayac-btn" onclick="sayiDegis('husher', 1)">+</button>
            </div>
        </div>

        <div class="kart satir">
            <div><div style="font-weight:700;">Konum gösterme</div><div style="font-size:12px; color:#888;">Kaç dakikada bir</div></div>
            <div class="seg-grup" id="grp_konum">
                <button class="seg-btn secili" onclick="segSec('konum', 2, this)">2</button>
                <button class="seg-btn" onclick="segSec('konum', 3, this)">3</button>
                <button class="seg-btn" onclick="segSec('konum', 5, this)">5</button>
            </div>
        </div>

        <div class="kart satir">
            <div><div style="font-weight:700;">Alan daralması</div><div style="font-size:12px; color:#888;">Her 5 dk'da bir daralır</div></div>
            <label class="switch"><input type="checkbox" id="sw_daralma" checked><span class="slider"></span></label>
        </div>

        <div class="kart satir">
            <div><div style="font-weight:700;">Fotoğraf görevleri</div><div style="font-size:12px; color:#888;">Husher'ı çek, ekstra XP kazan</div></div>
            <label class="switch"><input type="checkbox" id="sw_foto" checked><span class="slider"></span></label>
        </div>

        <button class="btn-siyah" onclick="alanSecimeGit()">Devam: alanı seç  →</button>
    </div>

    <!-- 3. EKRAN: OYUN ALANI SEÇ -->
    <div id="ekran_alan" class="ekran">
        <div class="satir" style="margin-bottom:10px;">
            <button onclick="ekranGec('ekran_kur')" style="background:#fff; border:none; width:40px; height:40px; border-radius:50%; font-size:20px;">‹</button>
            <div style="background:#fff; flex:1; margin-left:10px; padding:10px 16px; border-radius:20px; font-weight:600;">🔍 Haritaya dokunarak merkezi seç</div>
        </div>

        <div style="position:relative;">
            <div id="harita_secim"></div>
            <button class="harita-odak-btn" onclick="secimKonumaOdakla()">🎯</button>
        </div>

        <div class="kart" style="margin-top:-16px; z-index:2;">
            <div class="satir">
                <div>
                    <div style="font-weight:800; font-size:20px;">Oyun alanı</div>
                    <div id="yaricap_bilgi" style="font-size:13px; color:#666;">Yarıçap 450 m • 0,64 km²</div>
                </div>
                <span class="badge-hazir">✓ HD Harita</span>
            </div>
            <input type="range" id="rng_yaricap" min="100" max="1000" step="50" value="450" style="width:100%; margin:16px 0; accent-color:#16a34a;" oninput="yaricapGuncelle(this.value)">
            <div style="display:flex; gap:14px; font-size:12px; color:#555; margin-bottom:12px;">
                <span>🟢 Güvenli alan</span>
                <span>🔴 Oyun dışı</span>
                <span>➖ Daralma</span>
            </div>
            <button class="btn-siyah" onclick="odayiTamamla()">Alanı onayla</button>
        </div>
    </div>

    <!-- 4. EKRAN: LOBİ -->
    <div id="ekran_lobi" class="ekran">
        <div class="satir" style="margin-bottom:10px;">
            <button onclick="ekranGec('ekran_home')" style="background:none; border:none; font-size:22px;">‹</button>
            <span style="font-weight:800;">Lobi</span>
            <span>📤</span>
        </div>
        <div style="text-align:center; font-size:12px; color:#777;">Oda kodu</div>
        <div id="kod_kutulari" style="display:flex; justify-content:center; gap:8px; margin:10px 0 16px 0;"></div>

        <div style="display:flex; gap:10px; margin-bottom:16px;">
            <button class="btn-beyaz" style="margin:0; padding:12px;" onclick="navigator.clipboard.writeText(aktifKod); alert('Kod kopyalandı: '+aktifKod)">🔗 Davet linki</button>
            <button class="btn-beyaz" style="margin:0; padding:12px;" onclick="gpsBaslat()">📍 GPS Yenile</button>
        </div>

        <div class="satir" style="margin-bottom:8px;">
            <span id="lobi_oyuncu_sayisi" style="font-weight:800; font-size:18px;">Oyuncular 1/8</span>
            <span id="lobi_ozet" style="font-size:12px; color:#777;">20 dk • 2 husher</span>
        </div>

        <div id="lobi_liste" style="flex:1; overflow-y:auto;"></div>

        <div style="text-align:center; font-size:12px; color:#888; margin:8px 0;">GPS bir kez onaylandığında hep açık kalır</div>
        <button id="btn_oyunu_baslat" class="btn-siyah" onclick="oyunuBaslat()">OYUNU BAŞLAT</button>
    </div>

    <!-- 5. EKRAN: SAKLAN! SİYAH EKRAN -->
    <div id="ekran_saklan" class="ekran" style="background:#0a0a0a; color:#fff; text-align:center; justify-content:center; align-items:center;">
        <h1 id="saklan_baslik" style="font-size:44px; font-weight:900; margin:0;">SAKLAN!</h1>
        <p id="saklan_alt" style="color:#aaa; margin-top:6px;">Husher'lar henüz kimseyi göremiyor.</p>

        <div style="width:210px; height:210px; border-radius:50%; border:7px solid #fff; display:flex; flex-direction:column; align-items:center; justify-content:center; margin:24px 0;">
            <div id="saklan_sayac" style="font-size:48px; font-weight:900;">03:00</div>
            <div id="saklan_toplam" style="font-size:13px; color:#888;">/ 03:00</div>
        </div>

        <div style="background:#14291a; border:1px solid #22c55e; border-radius:16px; padding:14px 20px; width:100%; display:flex; align-items:center; gap:12px; text-align:left;">
            <span style="background:#22c55e; color:#000; border-radius:6px; padding:4px 8px; font-weight:bold;">✓</span>
            <div>
                <div style="font-weight:700; color:#4ade80;">Oyun alanının içindesin</div>
                <div id="saklan_mesafe" style="font-size:12px; color:#86efac;">Sınıra 310 m • GPS ±4 m</div>
            </div>
        </div>
        <button class="btn-beyaz" style="background:#1a1a1a; color:#fff; border-color:#333; margin-top:16px;" onclick="cepModuAc()">🌙 Cep Modu (Cebe Koyarken Bas)</button>
    </div>

    <!-- 6. EKRAN: AKTİF OYUN -->
    <div id="ekran_oyun" class="ekran" style="padding:12px;">
        <div id="ust_bar_normal" class="kart" style="margin-bottom:8px;">
            <div class="satir">
                <div><div style="font-size:11px; color:#888;">Kalan süre</div><div id="oyun_kalan_sure" style="font-size:28px; font-weight:900;">14:32</div></div>
                <div style="text-align:center;"><div style="font-size:11px; color:#888;">Kalan saklanan</div><div id="oyun_kalan_kisi" style="font-size:24px; font-weight:900;">4/5</div></div>
                <div style="text-align:right;"><div style="font-size:11px; color:#888;">Puan</div><div id="oyun_puan" style="font-size:24px; font-weight:900; color:#16a34a;">1.240</div></div>
            </div>
            <div class="satir" style="margin-top:8px;">
                <span id="oyun_rol_etiket" style="background:#111; color:#fff; padding:4px 12px; border-radius:12px; font-size:11px; font-weight:800;">SAKLANAN</span>
                <span id="oyun_daralma_sayac" style="font-size:12px; color:#666;">Daralma 01:12</span>
            </div>
        </div>

        <div id="ust_bar_kirmizi" class="kart" style="background:#991b1b; color:#fff; display:none; margin-bottom:8px;">
            <div class="satir">
                <div>
                    <div style="font-size:11px; font-weight:700; color:#fca5a5;">⚠ ALAN DARALIYOR</div>
                    <div id="kirmizi_sayac" style="font-size:32px; font-weight:900;">00:58</div>
                </div>
                <div style="text-align:right; font-size:12px; color:#fecaca;">
                    <div id="daralma_kacinci">Dikkat!</div>
                    <div id="daralma_yeni_r">Yeni yarıçap 300 m</div>
                </div>
            </div>
        </div>

        <div style="position:relative; flex:1;">
            <div id="oyun_harita"></div>
            <div id="konum_uyari_balonu" style="position:absolute; top:12px; left:50%; transform:translateX(-50%); background:rgba(255,255,255,0.95); backdrop-filter:blur(6px); padding:8px 14px; border-radius:20px; font-size:12px; font-weight:600; box-shadow:0 4px 15px rgba(0,0,0,0.12); z-index:500; white-space:nowrap;">
                Husher'lar seni <b>burada</b> görüyor
            </div>
            <button class="harita-odak-btn" onclick="oyunKonumaOdakla()">🎯</button>
        </div>

        <!-- HIZLI TAKTİK MESAJLARI BARİ -->
        <div class="hizli-mesaj-bar">
            <button class="hizli-chip" onclick="hizliMesajGonder('Çok yaklaştın! 🎯')">🎯 Çok yaklaştın!</button>
            <button class="hizli-chip" onclick="hizliMesajGonder('Beni bulamazsın! 👻')">👻 Beni bulamazsın!</button>
            <button class="hizli-chip" onclick="hizliMesajGonder('Buradayım, gel al! 🏃‍♂️')">🏃‍♂️ Buradayım!</button>
            <button class="hizli-chip" onclick="sahteSinyalGonder()">📍 Sahte Sinyal At</button>
        </div>

        <div id="alan_disi_kart" class="kart" style="display:none; margin-top:8px; border:2px solid #ef4444;">
            <div style="display:flex; gap:10px; align-items:center;">
                <div style="background:#fee2e2; padding:10px; border-radius:12px; font-size:20px;">🚶</div>
                <div>
                    <div style="color:#dc2626; font-weight:800;">Yeni alanın dışındasın</div>
                    <div id="alan_disi_yon" style="font-size:13px; color:#444;">80 m güneybatıya ilerle. Yürü, koşma.</div>
                    <div style="font-size:11px; color:#888;">Daralmadan sonra 60 saniye ek süren var.</div>
                </div>
            </div>
            <button class="btn-siyah" style="margin-top:10px; padding:12px;" onclick="haritaMerkezle()">➤ Güvenli rotayı göster</button>
        </div>

        <div id="alt_aksiyon_bar" style="display:flex; gap:8px; margin-top:8px;">
            <input type="file" accept="image/*" capture="environment" id="kamera_girdi" style="display:none" onchange="husherFotografla()">
            <button id="btn_foto_cek" class="btn-siyah" style="flex:1.3; margin:0; padding:14px;" onclick="document.getElementById('kamera_girdi').click()">📷 Fotoğrafla</button>
            <button id="btn_yakalandim" class="btn-beyaz" style="flex:1; margin:0; padding:14px;" onclick="yakalandimBildir()">🏁 Yakalandım</button>
        </div>
        <button class="btn-beyaz" style="background:#111; color:#fff; margin-top:8px; padding:13px;" onclick="cepModuAc()">🌙 Cep Modu (Cebe Koyarken Bas)</button>
    </div>

    <!-- 7. EKRAN: FOTOĞRAF ONAY ( +100 XP ) -->
    <div id="ekran_foto_onay" class="ekran" style="justify-content:flex-end; background:rgba(0,0,0,0.85);">
        <div class="kart" style="padding:24px; border-radius:24px;">
            <div style="width:44px; height:44px; background:#dcfce7; color:#16a34a; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:bold; margin-bottom:12px;">✓</div>
            <h2 style="margin:0; font-size:24px; font-weight:900;">HUSHER'I ÇEKTİN!</h2>
            <p style="color:#666; font-size:14px; margin:4px 0 16px 0;">Husher çekenin sen olduğunu bilmeyecek.</p>
            <div class="satir" style="border-top:1px solid #eee; border-bottom:1px solid #eee; padding:14px 0; margin-bottom:14px;">
                <span style="font-size:36px; font-weight:900; color:#16a34a;">+100 XP</span>
                <div style="text-align:right; font-size:12px; color:#777;">Sonraki fotoğraf<br><b>+25 XP • 03:00 sonra</b></div>
            </div>
            <div style="background:#f5f5f3; padding:10px; border-radius:12px; font-size:12px; color:#555; margin-bottom:14px;">
                🛡 Sadece HUSH etiketleri doğrulanır. Yüzler asla taranmaz.
            </div>
            <button class="btn-siyah" onclick="ekranGec('ekran_oyun')">Haritaya dön</button>
        </div>
    </div>

    <!-- 8. EKRAN: OYUN BİTTİ & SIRALAMA -->
    <div id="ekran_bitti" class="ekran" style="background:#0f0f0f; color:#fff; text-align:center;">
        <div style="margin-top:20px; font-size:54px;">🏆</div>
        <div id="bitti_etiket" style="display:inline-block; margin:8px auto; background:#22c55e; color:#000; font-weight:900; font-size:12px; padding:5px 14px; border-radius:20px;">OYUN SONA ERDİ</div>
        <h1 id="bitti_kazanan_baslik" style="font-size:32px; font-weight:900; margin:6px 0;">SAKLANANLAR KAZANDI!</h1>
        <p id="bitti_aciklama" style="color:#aaa; font-size:14px; margin:0 0 20px 0;">Süre doldu ve saklananlar hayatta kaldı.</p>

        <div style="text-align:left; font-size:13px; font-weight:800; color:#888; margin-bottom:8px;">MAÇ SIRALAMASI (XP)</div>
        <div id="bitti_siralama_liste" style="flex:1; overflow-y:auto; margin-bottom:14px;"></div>

        <button class="btn-beyaz" style="background:#22c55e; color:#000; border:none;" onclick="tekrarOyna()">🔄 Aynı Odada Tekrar Oyna</button>
        <button class="btn-siyah" style="background:#1f1f1f; border:1px solid #333;" onclick="ekranGec('ekran_home')">Ana Ekrana Dön</button>
    </div>

</div>

<script>
let ayarlar = { oyuncu: 8, sure: 20, saklanma: 3, husher: 2, konum: 2, yaricap: 450 };
let oyuncuAdi = "", aktifKod = "", gpsAcik = false, lat = 41.2867, lon = 36.3300;
let haritaSecim = null, secimDaire = null, secimMarker = null;
let oyunHarita = null, oyunDaire = null, icDaire = null, oyuncuMarker = null, husherPinleri = [];
let sonPinImzasi = "";
let takipTimer = null, gpsIzleyici = null, uykuKilidi = null, sonTiklama = 0;

let sesCtx = null;
let oncekiFaz = "";
let oncekiPeriyot = -1;
let oncekiAlan = -1;
let oncekiAlanDisi = false;
let sonMesajSayisi = 0;

const HARITA_URL = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';

const oyuncuIkon = L.divIcon({
    className: '',
    html: '<div class="oyuncu-radar"><div class="oyuncu-dalga"></div><div class="oyuncu-merkez"></div></div>',
    iconSize: [22, 22],
    iconAnchor: [11, 11]
});

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
}

function sesHazirla() {
    try {
        if (!sesCtx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) sesCtx = new AudioCtx();
        }
        if (sesCtx && sesCtx.state === 'suspended') {
            sesCtx.resume();
        }
    } catch (e) {}
}

function uyariVer(tip) {
    if ('vibrate' in navigator) {
        try {
            if (tip === 'konum') {
                navigator.vibrate([200, 100, 200]);
            } else if (tip === 'daralma') {
                navigator.vibrate([350, 120, 350, 120, 350]);
            } else if (tip === 'basladi') {
                navigator.vibrate(600);
            } else if (tip === 'bitti') {
                navigator.vibrate([400, 150, 400, 150, 600]);
            } else if (tip === 'mesaj') {
                navigator.vibrate(100);
            }
        } catch (e) {}
    }

    try {
        sesHazirla();
        if (sesCtx) {
            const osc = sesCtx.createOscillator();
            const gain = sesCtx.createGain();
            osc.connect(gain);
            gain.connect(sesCtx.destination);

            if (tip === 'konum') {
                osc.frequency.setValueAtTime(880, sesCtx.currentTime);
                gain.gain.setValueAtTime(0.15, sesCtx.currentTime);
                osc.start();
                osc.stop(sesCtx.currentTime + 0.18);
            } else if (tip === 'daralma') {
                osc.frequency.setValueAtTime(440, sesCtx.currentTime);
                osc.frequency.setValueAtTime(660, sesCtx.currentTime + 0.15);
                gain.gain.setValueAtTime(0.2, sesCtx.currentTime);
                osc.start();
                osc.stop(sesCtx.currentTime + 0.35);
            } else if (tip === 'basladi') {
                osc.frequency.setValueAtTime(587, sesCtx.currentTime);
                gain.gain.setValueAtTime(0.2, sesCtx.currentTime);
                osc.start();
                osc.stop(sesCtx.currentTime + 0.4);
            } else if (tip === 'bitti') {
                osc.frequency.setValueAtTime(523, sesCtx.currentTime);
                osc.frequency.setValueAtTime(659, sesCtx.currentTime + 0.15);
                osc.frequency.setValueAtTime(784, sesCtx.currentTime + 0.30);
                gain.gain.setValueAtTime(0.25, sesCtx.currentTime);
                osc.start();
                osc.stop(sesCtx.currentTime + 0.55);
            } else if (tip === 'mesaj') {
                osc.frequency.setValueAtTime(750, sesCtx.currentTime);
                gain.gain.setValueAtTime(0.1, sesCtx.currentTime);
                osc.start();
                osc.stop(sesCtx.currentTime + 0.1);
            }
        }
    } catch (e) {}
}

async function ekranAcikTut() {
    try {
        if ('wakeLock' in navigator && !uykuKilidi) {
            uykuKilidi = await navigator.wakeLock.request('screen');
            uykuKilidi.addEventListener('release', () => { uykuKilidi = null; });
        }
    } catch (err) {}
}

function cepModuAc() {
    ekranAcikTut();
    sesHazirla();
    gpsBaslat();
    document.getElementById('cep_modu_katman').style.display = 'flex';
}

function cepModuTiklama() {
    let simdi = new Date().getTime();
    if (simdi - sonTiklama < 400) {
        document.getElementById('cep_modu_katman').style.display = 'none';
    }
    sonTiklama = simdi;
}

document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        ekranAcikTut();
        gpsBaslat();
        if(aktifKod) sunucuDurumCek();
    }
});

window.addEventListener('load', () => {
    const kayitliIsim = localStorage.getItem('hush_isim');
    if (kayitliIsim) document.getElementById('oyuncu_ismi').value = kayitliIsim;

    if (navigator.permissions && navigator.permissions.query) {
        navigator.permissions.query({ name: 'geolocation' }).then(res => {
            if (res.state === 'granted') {
                gpsBaslat();
            }
        });
    }
    if (localStorage.getItem('hush_gps_izin') === 'evet') {
        gpsBaslat();
    }
});

function gpsBaslat() {
    ekranAcikTut();
    if (!navigator.geolocation) return;
    if (gpsIzleyici !== null) navigator.geolocation.clearWatch(gpsIzleyici);

    gpsIzleyici = navigator.geolocation.watchPosition(pos => {
        lat = pos.coords.latitude;
        lon = pos.coords.longitude;
        gpsAcik = true;
        localStorage.setItem('hush_gps_izin', 'evet');
        const dEl = document.getElementById('ana_gps_durum');
        if (dEl) dEl.innerText = `GPS Aktif (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
        if (oyunHarita && oyuncuMarker) {
            oyuncuMarker.setLatLng([lat, lon]);
        }
    }, () => {
        gpsAcik = true;
    }, { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 });
    gpsAcik = true;
}

function ekranGec(id) {
    document.querySelectorAll('.ekran').forEach(e => e.classList.remove('aktif'));
    document.getElementById(id).classList.add('aktif');
    if(id === 'ekran_alan') setTimeout(haritaSecimKur, 150);
    if(id === 'ekran_oyun') setTimeout(oyunHaritaKur, 150);
}

function sayiDegis(tip, fark) {
    if(tip === 'oyuncu') {
        ayarlar.oyuncu = Math.min(20, Math.max(4, ayarlar.oyuncu + fark));
        document.getElementById('val_oyuncu').innerText = ayarlar.oyuncu;
    } else {
        ayarlar.husher = Math.min(5, Math.max(1, ayarlar.husher + fark));
        document.getElementById('val_husher').innerText = ayarlar.husher;
    }
}

function segSec(tip, deger, btn) {
    ayarlar[tip] = deger;
    btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('secili'));
    btn.classList.add('secili');
}

function alanSecimeGit() {
    gpsBaslat();
    ekranGec('ekran_alan');
}

function haritaSecimKur() {
    if(!haritaSecim) {
        haritaSecim = L.map('harita_secim', {
            zoomControl: false,
            zoomAnimation: true,
            fadeAnimation: true,
            inertia: true,
            preferCanvas: true
        }).setView([lat, lon], 16);

        L.tileLayer(HARITA_URL, {
            maxZoom: 20,
            detectRetina: true,
            updateWhenIdle: false,
            keepBuffer: 4
        }).addTo(haritaSecim);

        secimDaire = L.circle([lat, lon], {
            radius: ayarlar.yaricap,
            color: '#16a34a',
            weight: 3,
            fillColor: '#22c55e',
            fillOpacity: 0.18
        }).addTo(haritaSecim);

        secimMarker = L.marker([lat, lon], {icon: oyuncuIkon}).addTo(haritaSecim);

        haritaSecim.on('click', e => {
            lat = e.latlng.lat; lon = e.latlng.lng;
            secimDaire.setLatLng(e.latlng);
            secimMarker.setLatLng(e.latlng);
            haritaSecim.panTo(e.latlng, {animate: true, duration: 0.4});
        });
    } else {
        haritaSecim.setView([lat, lon], 16);
        secimDaire.setLatLng([lat, lon]);
        secimMarker.setLatLng([lat, lon]);
    }
    setTimeout(() => haritaSecim.invalidateSize(), 150);
}

function secimKonumaOdakla() {
    if(haritaSecim) {
        haritaSecim.flyTo([lat, lon], 17, {animate: true, duration: 0.8});
        secimDaire.setLatLng([lat, lon]);
        secimMarker.setLatLng([lat, lon]);
    }
}

function oyunKonumaOdakla() {
    if(oyunHarita) {
        oyunHarita.flyTo([lat, lon], 17, {animate: true, duration: 0.8});
    }
}

function yaricapGuncelle(val) {
    ayarlar.yaricap = parseInt(val);
    let km2 = ((Math.PI * val * val) / 1000000).toFixed(2).replace('.', ',');
    document.getElementById('yaricap_bilgi').innerText = `Yarıçap ${val} m • ${km2} km²`;
    if(secimDaire) secimDaire.setRadius(ayarlar.yaricap);
}

async function odayiTamamla() {
    oyuncuAdi = document.getElementById('oyuncu_ismi').value.trim() || "Mert Efe";
    localStorage.setItem('hush_isim', oyuncuAdi);
    ayarlar.daralma = document.getElementById('sw_daralma').checked;
    ayarlar.foto = document.getElementById('sw_foto').checked;
    ayarlar.kurucu = oyuncuAdi;
    ayarlar.merkez_lat = lat;
    ayarlar.merkez_lon = lon;

    let res = await fetch('/oda_kur', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(ayarlar)});
    let d = await res.json();
    aktifKod = d.kod;
    lobiAc();
}

async function odayaKatil() {
    oyuncuAdi = document.getElementById('oyuncu_ismi').value.trim() || "Oyuncu_" + Math.floor(Math.random()*90+10);
    localStorage.setItem('hush_isim', oyuncuAdi);
    aktifKod = document.getElementById('girilen_kod').value.trim();
    if(aktifKod.length !== 6) { alert("6 haneli oda kodunu girin!"); return; }
    let res = await fetch('/katil', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi})});
    let d = await res.json();
    if(d.hata) { alert(d.hata); return; }
    gpsBaslat();
    lobiAc();
}

function lobiAc() {
    ekranGec('ekran_lobi');
    let kutular = "";
    for(let i=0; i<6; i++) kutular += `<div class="kod-kutu">${aktifKod[i]}</div>`;
    document.getElementById('kod_kutulari').innerHTML = kutular;
    if(takipTimer) clearInterval(takipTimer);
    takipTimer = setInterval(sunucuDurumCek, 1000);
}

async function oyunuBaslat() {
    sesHazirla();
    await fetch('/baslat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod})});
}

async function tekrarOyna() {
    await fetch('/tekrar_oyna', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod})});
    oncekiFaz = "";
    oncekiPeriyot = -1;
    oncekiAlan = -1;
    sonMesajSayisi = 0;
    ekranGec('ekran_lobi');
}

async function hizliMesajGonder(mesaj) {
    await fetch('/mesaj_gonder', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi, mesaj:mesaj})});
}

async function sahteSinyalGonder() {
    // Bulunduğun konumun 40-80 metre yakınına sahte bir sapma vererek sinyal at
    let rastgeleAci = Math.random() * Math.PI * 2;
    let rastgeleMesafe = 40 + Math.random() * 40;
    let sahteLat = lat + (rastgeleMesafe / 111320) * Math.cos(rastgeleAci);
    let sahteLon = lon + (rastgeleMesafe / (111320 * Math.cos(lat * Math.PI / 180))) * Math.sin(rastgeleAci);

    await fetch('/sahte_sinyal', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi, lat:sahteLat, lon:sahteLon})});
    alert("📍 Sahte konum sinyali haritaya fırlatıldı!");
}

function oyunHaritaKur() {
    if(!oyunHarita) {
        oyunHarita = L.map('oyun_harita', {
            zoomControl: false,
            zoomAnimation: true,
            fadeAnimation: true,
            inertia: true,
            preferCanvas: true
        }).setView([lat, lon], 16);

        L.tileLayer(HARITA_URL, {
            maxZoom: 20,
            detectRetina: true,
            updateWhenIdle: false,
            keepBuffer: 4
        }).addTo(oyunHarita);

        oyunDaire = L.circle([lat, lon], {
            radius: ayarlar.yaricap,
            color: '#16a34a',
            weight: 3,
            fillColor: '#22c55e',
            fillOpacity: 0.14
        }).addTo(oyunHarita);

        icDaire = L.circle([lat, lon], {
            radius: ayarlar.yaricap * 0.75,
            color: '#0f0f0f',
            weight: 2,
            dashArray: '6, 8',
            fill: false
        }).addTo(oyunHarita);

        oyuncuMarker = L.marker([lat, lon], {icon: oyuncuIkon, zIndexOffset: 1000}).addTo(oyunHarita);
    }
    setTimeout(() => oyunHarita.invalidateSize(), 150);
}

function haritaMerkezle() {
    if(oyunHarita && oyunDaire) oyunHarita.flyTo(oyunDaire.getLatLng(), 16, {animate: true, duration: 0.8});
}

async function husherFotografla() {
    await fetch('/foto_xp', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi})});
    ekranGec('ekran_foto_onay');
}

async function yakalandimBildir() {
    if(confirm("Husher tarafından yakalandığını onaylıyor musun?")) {
        await fetch('/yakalandim', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi})});
    }
}

async function sunucuDurumCek() {
    if(!aktifKod) return;
    let res = await fetch('/durum', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi, lat:lat, lon:lon, gps:gpsAcik})});
    let d = await res.json();
    if(d.hata) return;

    if(!d.basladi) {
        if(document.getElementById('ekran_bitti').classList.contains('aktif')) {
            ekranGec('ekran_lobi');
        }
        let isimler = Object.keys(d.oyuncular);
        document.getElementById('lobi_oyuncu_sayisi').innerText = `Oyuncular ${isimler.length}/${d.ayarlar.oyuncu}`;
        document.getElementById('lobi_ozet').innerText = `${d.ayarlar.sure} dk • ${d.ayarlar.husher} husher`;
        let listeHtml = "";
        isimler.forEach(isim => {
            let p = d.oyuncular[isim];
            let rozet = p.gps ? `<span class="badge-hazir">✓ Hazır</span>` : `<span class="badge-kapali">⚠ Konum kapalı</span>`;
            listeHtml += `<div class="kart satir" style="padding:12px 16px; margin-bottom:8px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="width:36px; height:36px; border-radius:50%; background:#eee; display:flex; align-items:center; justify-content:center; font-weight:bold;">${isim[0].toUpperCase()}</div>
                    <div><div style="font-weight:700;">${isim}</div><div style="font-size:11px; color:#888;">@${isim.toLowerCase().replace(' ','')}</div></div>
                </div>
                ${rozet}
            </div>`;
        });
        document.getElementById('lobi_liste').innerHTML = listeHtml;
    } else {
        let ben = d.oyuncular[oyuncuAdi];

        if (oncekiFaz === "SAKLANMA" && d.faz === "OYUN") {
            uyariVer('basladi');
        }
        if (oncekiFaz !== "BITTI" && d.faz === "BITTI") {
            document.getElementById('cep_modu_katman').style.display = 'none';
            uyariVer('bitti');
        }
        oncekiFaz = d.faz;

        // Yeni gelen mesajları kontrol et ve uyarı ver
        if (d.mesajlar && d.mesajlar.length > sonMesajSayisi) {
            if (sonMesajSayisi > 0) {
                let sonMsg = d.mesajlar[d.mesajlar.length - 1];
                if (sonMsg.gonderen !== oyuncuAdi) {
                    uyariVer('mesaj');
                    document.getElementById('konum_uyari_balonu').innerHTML = `💬 <b>${sonMsg.gonderen}</b>: ${sonMsg.mesaj}`;
                }
            }
            sonMesajSayisi = d.mesajlar.length;
        }

        if(d.faz === "SAKLANMA") {
            if(!document.getElementById('ekran_saklan').classList.contains('aktif')) ekranGec('ekran_saklan');
            document.getElementById('saklan_baslik').innerText = (ben.rol === "HUSHER") ? "BEKLE!" : "SAKLAN!";
            document.getElementById('saklan_alt').innerText = (ben.rol === "HUSHER") ? "Saklananlar yerleşiyor, hareket etme!" : "Husher'lar henüz kimseyi göremiyor.";
            document.getElementById('saklan_sayac').innerText = d.saklanma_sayac;
            document.getElementById('cep_sayac_bilgi').innerText = d.saklanma_sayac;
            document.getElementById('saklan_toplam').innerText = `/ 0${d.ayarlar.saklanma}:00`;
            document.getElementById('saklan_mesafe').innerText = `Sınıra ${Math.max(0, d.aktif_alan - ben.mesafe)} m • GPS ±4 m`;
        } else if(d.faz === "BITTI") {
            if(!document.getElementById('ekran_bitti').classList.contains('aktif')) ekranGec('ekran_bitti');
            document.getElementById('bitti_kazanan_baslik').innerText = d.kazanan_baslik;
            document.getElementById('bitti_aciklama').innerText = d.kazanan_aciklama;
            document.getElementById('ana_xp').innerText = ben.xp;

            let sirali = Object.entries(d.oyuncular).sort((a, b) => b[1].xp - a[1].xp);
            let siraHtml = "";
            sirali.forEach((item, idx) => {
                let isim = item[0];
                let p = item[1];
                let durumYazi = (p.ilk_rol === "HUSHER") ? "👁 Husher" : (p.yakalandi ? "🏁 Yakalandı" : "🛡 Hayatta Kaldı");
                let madalya = idx === 0 ? "🥇" : (idx === 1 ? "🥈" : (idx === 2 ? "🥉" : `#${idx+1}`));
                siraHtml += `<div style="background:#1a1a1a; border:1px solid #2a2a2a; border-radius:14px; padding:12px 16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:12px;">
                        <span style="font-size:20px; font-weight:900;">${madalya}</span>
                        <div style="text-align:left;">
                            <div style="font-weight:800; color:#fff;">${isim}</div>
                            <div style="font-size:11px; color:#888;">${durumYazi}</div>
                        </div>
                    </div>
                    <div style="font-size:18px; font-weight:900; color:#4ade80;">${p.xp} XP</div>
                </div>`;
            });
            document.getElementById('bitti_siralama_liste').innerHTML = siraHtml;
        } else {
            if(document.getElementById('ekran_saklan').classList.contains('aktif') || document.getElementById('ekran_lobi').classList.contains('aktif')) {
                ekranGec('ekran_oyun');
            }

            if (d.periyot_no !== undefined && d.periyot_no !== oncekiPeriyot) {
                if (oncekiPeriyot !== -1) {
                    uyariVer('konum');
                }
                oncekiPeriyot = d.periyot_no;
            }

            if (oncekiAlan !== -1 && d.aktif_alan < oncekiAlan) {
                uyariVer('daralma');
            }
            oncekiAlan = d.aktif_alan;

            if (!oncekiAlanDisi && ben.alan_disi) {
                uyariVer('daralma');
            }
            oncekiAlanDisi = ben.alan_disi;

            document.getElementById('oyun_kalan_sure').innerText = d.oyun_sayac;
            document.getElementById('cep_sayac_bilgi').innerText = d.oyun_sayac;
            document.getElementById('oyun_kalan_kisi').innerText = `${d.kalan_saklanan}/${d.toplam_saklanan}`;
            document.getElementById('oyun_puan').innerText = ben.xp;
            document.getElementById('oyun_rol_etiket').innerText = ben.rol;
            document.getElementById('oyun_daralma_sayac').innerText = `Daralma ${d.daralma_sayac}`;
            if(sonMesajSayisi === 0) {
                document.getElementById('konum_uyari_balonu').innerHTML = `Son konum bildirimi • <b>${d.konum_sayac}</b> sonra`;
            }

            if(ben.alan_disi) {
                document.getElementById('ust_bar_normal').style.display = 'none';
                document.getElementById('ust_bar_kirmizi').style.display = 'block';
                document.getElementById('kirmizi_sayac').innerText = d.daralma_sayac;
                document.getElementById('daralma_yeni_r').innerText = `Yeni yarıçap ${d.aktif_alan} m`;
                document.getElementById('alan_disi_kart').style.display = 'block';
                document.getElementById('alan_disi_yon').innerText = `${ben.mesafe - d.aktif_alan} m ${ben.yon} ilerle. Yürü, koşma.`;
            } else {
                document.getElementById('ust_bar_normal').style.display = 'block';
                document.getElementById('ust_bar_kirmizi').style.display = 'none';
                document.getElementById('alan_disi_kart').style.display = 'none';
            }

            if(oyunHarita) {
                oyunDaire.setLatLng([d.merkez_lat, d.merkez_lon]);
                oyunDaire.setRadius(d.aktif_alan);
                icDaire.setLatLng([d.merkez_lat, d.merkez_lon]);
                icDaire.setRadius(Math.max(40, d.aktif_alan * 0.75));
                oyuncuMarker.setLatLng([lat, lon]);

                let yeniPinImza = JSON.stringify(d.bildirilen_pinler) + "_" + JSON.stringify(d.sahte_pinler) + "_" + ben.rol;
                if(yeniPinImza !== sonPinImzasi) {
                    sonPinImzasi = yeniPinImza;
                    husherPinleri.forEach(p => oyunHarita.removeLayer(p));
                    husherPinleri = [];

                    // Gerçek Konum Pini (Sadece Husher'a görünür)
                    if(ben.rol === "HUSHER") {
                        d.bildirilen_pinler.forEach(pin => {
                            let hIkon = L.divIcon({
                                className: '',
                                html: `<div class="hedef-pin"><div class="hedef-etiket">${pin.isim}</div><div class="hedef-dalga"></div><div class="hedef-merkez"></div></div>`,
                                iconSize: [24, 24],
                                iconAnchor: [12, 12]
                            });
                            let m = L.marker([pin.lat, pin.lon], {icon: hIkon}).addTo(oyunHarita);
                            husherPinleri.push(m);
                        });
                    }

                    // Sahte Sinyal Pinleri (Herkese görünür, kafa karıştırır!)
                    if(d.sahte_pinler) {
                        d.sahte_pinler.forEach(pin => {
                            let sIkon = L.divIcon({
                                className: '',
                                html: `<div class="hedef-pin" style="filter: hue-rotate(90deg);"><div class="hedef-etiket">⚡ ${pin.isim} (Sinyal)</div><div class="hedef-dalga"></div><div class="hedef-merkez"></div></div>`,
                                iconSize: [24, 24],
                                iconAnchor: [12, 12]
                            });
                            let m = L.marker([pin.lat, pin.lon], {icon: sIkon}).addTo(oyunHarita);
                            husherPinleri.push(m);
                        });
                    }
                }
            }
        }
    }
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_KODU)

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "HUSH - Canlı Saklambaç",
        "short_name": "HUSH",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f5f5f3",
        "theme_color": "#0f0f0f",
        "icons": [
            {
                "src": "https://img.icons8.com/ios-filled/512/ffffff/marker.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })

@app.route('/sw.js')
def service_worker():
    sw_code = """
    self.addEventListener('fetch', function(event) {
        // PWA Bridge
    });
    """
    return sw_code, 200, {'Content-Type': 'application/javascript'}

@app.route('/oda_kur', methods=['POST'])
def oda_kur():
    v = request.json
    kod = ''.join(random.choices("0123456789", k=6))
    odalar[kod] = {
        "ayarlar": v,
        "basladi": False,
        "bitti": False,
        "odul_verildi": False,
        "baslangic": 0,
        "merkez_lat": v.get("merkez_lat", 41.2867),
        "merkez_lon": v.get("merkez_lon", 36.3300),
        "son_periyot": -1,
        "bildirilen_pinler": [],
        "sahte_pinler": [],
        "mesajlar": [],
        "oyuncular": {
            v["kurucu"]: {"rol": "SAKLANAN", "ilk_rol": "SAKLANAN", "lat": v.get("merkez_lat", 41.2867), "lon": v.get("merkez_lon", 36.3300), "gps": True, "xp": 1240, "mesafe": 0, "alan_disi": False, "yakalandi": False, "yon": "merkeze"}
        }
    }
    return jsonify({"kod": kod})

@app.route('/katil', methods=['POST'])
def katil():
    v = request.json
    kod = v.get("kod")
    if kod not in odalar:
        return jsonify({"hata": "Oda bulunamadı!"})
    oda = odalar[kod]
    oda["oyuncular"][v["oyuncu"]] = {"rol": "SAKLANAN", "ilk_rol": "SAKLANAN", "lat": oda["merkez_lat"], "lon": oda["merkez_lon"], "gps": True, "xp": 1000, "mesafe": 0, "alan_disi": False, "yakalandi": False, "yon": "merkeze"}
    return jsonify({"basari": True})

@app.route('/baslat', methods=['POST'])
def baslat():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if not oda:
        return jsonify({"hata": "Oda yok"})
    oda["basladi"] = True
    oda["bitti"] = False
    oda["odul_verildi"] = False
    oda["baslangic"] = time.time()
    oda["son_periyot"] = -1
    oda["bildirilen_pinler"] = []
    oda["sahte_pinler"] = []
    oda["mesajlar"] = []
    isimler = list(oda["oyuncular"].keys())
    husher_sayisi = min(oda["ayarlar"]["husher"], max(1, len(isimler) - 1)) if len(isimler) > 1 else 0
    secilen_husherlar = random.sample(isimler, husher_sayisi)
    for isim, p in oda["oyuncular"].items():
        rol = "HUSHER" if isim in secilen_husherlar else "SAKLANAN"
        p["rol"] = rol
        p["ilk_rol"] = rol
        p["yakalandi"] = False
    return jsonify({"basari": True})

@app.route('/tekrar_oyna', methods=['POST'])
def tekrar_oyna():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if oda:
        oda["basladi"] = False
        oda["bitti"] = False
        oda["odul_verildi"] = False
        oda["bildirilen_pinler"] = []
        oda["sahte_pinler"] = []
        oda["mesajlar"] = []
        for isim, p in oda["oyuncular"].items():
            p["yakalandi"] = False
            p["rol"] = "SAKLANAN"
    return jsonify({"basari": True})

@app.route('/mesaj_gonder', methods=['POST'])
def mesaj_gonder():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if oda:
        oda["mesajlar"].append({"gonderen": v.get("oyuncu"), "mesaj": v.get("mesaj")})
        if len(oda["mesajlar"]) > 10:
            oda["mesajlar"].pop(0)
    return jsonify({"basari": True})

@app.route('/sahte_sinyal', methods=['POST'])
def sahte_sinyal():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if oda:
        oda["sahte_pinler"].append({"isim": v.get("oyuncu"), "lat": v.get("lat"), "lon": v.get("lon")})
        if len(oda["sahte_pinler"]) > 5:
            oda["sahte_pinler"].pop(0)
    return jsonify({"basari": True})

@app.route('/foto_xp', methods=['POST'])
def foto_xp():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if oda and v["oyuncu"] in oda["oyuncular"]:
        oda["oyuncular"][v["oyuncu"]]["xp"] += 100
    return jsonify({"basari": True})

@app.route('/yakalandim', methods=['POST'])
def yakalandim():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if oda and v["oyuncu"] in oda["oyuncular"]:
        oda["oyuncular"][v["oyuncu"]]["yakalandi"] = True
        oda["oyuncular"][v["oyuncu"]]["rol"] = "HUSHER"
    return jsonify({"basari": True})

@app.route('/durum', methods=['POST'])
def durum():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if not oda:
        return jsonify({"hata": "Oda yok"})

    oyuncu = v.get("oyuncu")
    if oyuncu in oda["oyuncular"]:
        p = oda["oyuncular"][oyuncu]
        p["lat"] = v.get("lat", oda["merkez_lat"])
        p["lon"] = v.get("lon", oda["merkez_lon"])
        p["gps"] = v.get("gps", True)

    if not oda["basladi"]:
        return jsonify({"basladi": False, "oyuncular": oda["oyuncular"], "ayarlar": oda["ayarlar"]})

    gecen = int(time.time() - oda["baslangic"])
    saklanma_sn = oda["ayarlar"]["saklanma"] * 60

    aktif_alan = oda["ayarlar"]["yaricap"]
    daralma_kalan = 300
    if gecen >= saklanma_sn:
        av_gecen = gecen - saklanma_sn
        daralma_kalan = 300 - (av_gecen % 300)
        if oda["ayarlar"].get("daralma", True):
            for _ in range(av_gecen // 300):
                aktif_alan = max(50, int(aktif_alan * 0.75))

    toplam_saklanan = 0
    kalan_saklanan = 0
    for isim, p in oda["oyuncular"].items():
        p["mesafe"] = int(mesafe_hesapla(oda["merkez_lat"], oda["merkez_lon"], p["lat"], p["lon"]))
        p["alan_disi"] = p["mesafe"] > aktif_alan
        p["yon"] = yon_hesapla(p["lat"], p["lon"], oda["merkez_lat"], oda["merkez_lon"])
        if p.get("ilk_rol") == "SAKLANAN":
            toplam_saklanan += 1
            if not p["yakalandi"]:
                kalan_saklanan += 1

    if gecen < saklanma_sn:
        return jsonify({
            "basladi": True,
            "faz": "SAKLANMA",
            "saklanma_sayac": sure_formatla(saklanma_sn - gecen),
            "aktif_alan": aktif_alan,
            "oyuncular": oda["oyuncular"],
            "ayarlar": oda["ayarlar"]
        })

    av_gecen = gecen - saklanma_sn
    oyun_kalan = (oda["ayarlar"]["sure"] * 60) - av_gecen

    if oyun_kalan <= 0 or (toplam_saklanan > 0 and kalan_saklanan == 0):
        if kalan_saklanan == 0 and toplam_saklanan > 0:
            kazanan_baslik = "HUSHER'LAR KAZANDI!"
            kazanan_aciklama = "Tüm saklanan oyuncular süre bitmeden yakalandı!"
            if not oda.get("odul_verildi"):
                for p in oda["oyuncular"].values():
                    if p.get("ilk_rol") == "HUSHER":
                        p["xp"] += 400
                oda["odul_verildi"] = True
        else:
            kazanan_baslik = "SAKLANANLAR KAZANDI!"
            kazanan_aciklama = f"Süre doldu ve {kalan_saklanan} oyuncu yakalanmadan hayatta kaldı!"
            if not oda.get("odul_verildi"):
                for p in oda["oyuncular"].values():
                    if p.get("ilk_rol") == "SAKLANAN" and not p["yakalandi"]:
                        p["xp"] += 500
                oda["odul_verildi"] = True

        return jsonify({
            "basladi": True,
            "faz": "BITTI",
            "kazanan_baslik": kazanan_baslik,
            "kazanan_aciklama": kazanan_aciklama,
            "oyuncular": oda["oyuncular"],
            "ayarlar": oda["ayarlar"]
        })

    konum_periyot = oda["ayarlar"]["konum"] * 60
    konum_kalan = konum_periyot - (av_gecen % konum_periyot)

    periyot_no = av_gecen // konum_periyot
    if periyot_no > oda["son_periyot"]:
        oda["son_periyot"] = periyot_no
        pinler = []
        for isim, p in oda["oyuncular"].items():
            if p["rol"] == "SAKLANAN" and not p["yakalandi"]:
                pinler.append({"isim": isim, "lat": p["lat"], "lon": p["lon"]})
        oda["bildirilen_pinler"] = pinler

    return jsonify({
        "basladi": True,
        "faz": "OYUN",
        "periyot_no": periyot_no,
        "oyun_sayac": sure_formatla(oyun_kalan),
        "daralma_sayac": sure_formatla(daralma_kalan),
        "konum_sayac": sure_formatla(konum_kalan),
        "aktif_alan": aktif_alan,
        "merkez_lat": oda["merkez_lat"],
        "merkez_lon": oda["merkez_lon"],
        "toplam_saklanan": max(1, toplam_saklanan),
        "kalan_saklanan": kalan_saklanan,
        "bildirilen_pinler": oda["bildirilen_pinler"],
        "sahte_pinler": oda["sahte_pinler"],
        "mesajlar": oda["mesajlar"],
        "oyuncular": oda["oyuncular"],
        "ayarlar": oda["ayarlar"]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
