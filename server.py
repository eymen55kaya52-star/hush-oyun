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
    <title>Hunting Game</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; user-select: none; }
        body { margin: 0; padding: 0; background: #f8f9fa; color: #111; display: flex; justify-content: center; }
        .telefon { width: 100%; max-width: 430px; min-height: 100vh; background: #f8f9fa; position: relative; display: flex; flex-direction: column; overflow-x: hidden; }
        .ekran { display: none; flex-direction: column; flex: 1; padding: 18px; }
        .aktif { display: flex; }
        .kart { background: #fff; border-radius: 20px; padding: 18px; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border: 1px solid #eee; }
        .btn-turuncu { background: linear-gradient(135deg, #f97316, #ea580c); color: #fff; border: none; border-radius: 18px; padding: 17px; font-size: 16px; font-weight: 700; width: 100%; cursor: pointer; box-shadow: 0 4px 12px rgba(249,115,22,0.3); }
        .btn-beyaz { background: #fff; color: #111; border: 1px solid #e2e2e2; border-radius: 16px; padding: 17px; font-size: 16px; font-weight: 700; width: 100%; cursor: pointer; }
        .satir { display: flex; justify-content: space-between; align-items: center; }
        .seg-grup { display: flex; background: #f1f1f1; border-radius: 14px; padding: 4px; gap: 4px; overflow-x: auto; }
        .seg-btn { border: none; background: transparent; padding: 10px 14px; border-radius: 10px; font-weight: 700; cursor: pointer; color: #666; font-size: 13px; white-space: nowrap; }
        .seg-btn.secili { background: #fff; color: #111; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .kod-giris { display: flex; justify-content: space-between; gap: 8px; margin: 15px 0; }
        .kod-input { width: 50px; height: 60px; background: #fff; border: 2px solid #e2e2e2; border-radius: 16px; text-align: center; font-size: 26px; font-weight: 800; outline: none; }
        .kod-input:focus { border-color: #f97316; }
        
        #harita_secim, #oyun_harita { 
            width: 100%; 
            height: 350px; 
            border-radius: 22px; 
            z-index: 1; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            border: 2px solid #fff;
            background: #aad3df;
        }
        .leaflet-control-attribution { display: none !important; }
        
        .oyuncu-radar {
            position: relative;
            width: 24px;
            height: 24px;
        }
        .oyuncu-merkez {
            width: 16px;
            height: 16px;
            background: #f97316;
            border: 3px solid #ffffff;
            border-radius: 50%;
            position: absolute;
            top: 4px;
            left: 4px;
            z-index: 2;
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        }
        .oyuncu-dalga {
            width: 24px;
            height: 24px;
            background: rgba(249, 115, 22, 0.45);
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
            width: 26px;
            height: 26px;
        }
        .hedef-merkez {
            width: 18px;
            height: 18px;
            background: #dc2626;
            border: 3px solid #ffffff;
            border-radius: 50%;
            position: absolute;
            top: 4px;
            left: 4px;
            z-index: 2;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.6);
        }
        .hedef-dalga {
            width: 26px;
            height: 26px;
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
            top: -26px;
            left: 50%;
            transform: translateX(-50%);
            background: #991b1b;
            color: #fff;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 8px;
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

        #cep_modu_katman {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: #000000;
            color: #333;
            z-index: 99999;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 20px;
        }
    </style>
</head>
<body onclick="ekranAcikTut(); sesHazirla();">

<div id="cep_modu_katman" onclick="cepModuTiklama()">
    <div style="font-size: 32px; margin-bottom: 10px;">🌙</div>
    <div style="font-weight: 800; font-size: 18px; color: #444;">HUNTING GAME - GİZLİ MOD</div>
    <div style="font-size: 13px; color: #666; margin-top: 8px;">GPS ve arka plan takibi aktif.<br>Ekrandan çıkmak için <b>iki kez dokun</b>.</div>
    <div id="cep_sayac_bilgi" style="font-size: 24px; font-weight: 900; color: #fff; margin-top: 25px;">--:--</div>
</div>

<div class="telefon">

    <!-- 1. EKRAN: ANA EKRAN & PROFİL -->
    <div id="ekran_home" class="ekran aktif">
        <div class="satir" style="margin-bottom: 20px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="background:#22c55e; color:#fff; width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:18px;" id="profil_harf">MU</div>
                <div>
                    <div id="profil_isim" style="font-weight:800; font-size:16px;">Musti</div>
                    <div style="font-size:12px; color:#666;">Level 6 • Scout</div>
                </div>
            </div>
            <button onclick="ekranGec('ekran_profil')" style="background:#fff; border:1px solid #eee; width:40px; height:40px; border-radius:50%; font-size:18px; cursor:pointer;">⚙️</button>
        </div>

        <div class="kart" style="background: linear-gradient(135deg, #f97316, #ea580c); color: #fff;">
            <div style="font-size:13px; opacity:0.9;">Coins • Maç içi güçlendirmeler için</div>
            <div style="font-size:28px; font-weight:900; margin-top:4px;">295</div>
        </div>

        <div class="kart">
            <div style="font-size:14px; font-weight:800; margin-bottom:12px;">Odaya Katıl</div>
            <div style="color:#666; font-size:12px; margin-bottom:6px;">Arkadaşının verdiği 5 haneli kod:</div>
            <div class="kod-giris">
                <input type="text" class="kod-input" maxlength="1" id="k1" oninput="kodIlerle(this, 'k2')">
                <input type="text" class="kod-input" maxlength="1" id="k2" oninput="kodIlerle(this, 'k3')">
                <input type="text" class="kod-input" maxlength="1" id="k3" oninput="kodIlerle(this, 'k4')">
                <input type="text" class="kod-input" maxlength="1" id="k4" oninput="kodIlerle(this, 'k5')">
                <input type="text" class="kod-input" maxlength="1" id="k5" oninput="odayaKatil()">
            </div>
        </div>

        <button class="btn-turuncu" onclick="gpsBaslat(); ekranGec('ekran_kur')">Start a new game</button>
    </div>

    <!-- 2. EKRAN: OYUN KUR / AYARLAR (MANHUNT) -->
    <div id="ekran_kur" class="ekran">
        <div class="satir" style="margin-bottom:15px;">
            <button onclick="ekranGec('ekran_home')" style="background:none; border:none; font-size:24px; cursor:pointer;">‹</button>
            <span style="font-weight:800; font-size:17px;">Game Setup</span>
            <span style="width:24px;"></span>
        </div>

        <div class="kart">
            <div style="font-weight:800; margin-bottom:4px;">What kind of hunt?</div>
            <div style="font-size:12px; color:#666; margin-bottom:12px;">Chasers track runners on the map.</div>
            <div style="font-weight:700; color:#ea580c;">✓ Manhunt (Avcı & Kaçan)</div>
        </div>

        <div class="kart">
            <div style="font-weight:800; margin-bottom:4px;">How long is the hunt?</div>
            <div style="font-size:12px; color:#666; margin-bottom:12px;">Chasers have this long to catch runners.</div>
            <div class="seg-grup" id="grp_sure">
                <button class="seg-btn" onclick="ayarSec('sure', 15, this)">15m</button>
                <button class="seg-btn" onclick="ayarSec('sure', 30, this)">30m</button>
                <button class="seg-btn secili" onclick="ayarSec('sure', 60, this)">1 hour</button>
                <button class="seg-btn" onclick="ayarSec('sure', 120, this)">2 hours</button>
            </div>
        </div>

        <div class="kart">
            <div style="font-weight:800; margin-bottom:4px;">Location updates</div>
            <div style="font-size:12px; color:#666; margin-bottom:12px;">Chasers get runner updates at this interval.</div>
            <div class="seg-grup" id="grp_konum">
                <button class="seg-btn" onclick="ayarSec('konum', 0.5, this)">30s</button>
                <button class="seg-btn" onclick="ayarSec('konum', 1, this)">1m</button>
                <button class="seg-btn secili" onclick="ayarSec('konum', 2, this)">2m</button>
                <button class="seg-btn" onclick="ayarSec('konum', 5, this)">5m</button>
            </div>
        </div>

        <button class="btn-turuncu" onclick="ekranGec('ekran_alan')">Continue to Map Zone</button>
    </div>

    <!-- 3. EKRAN: HARİTA ALANI SEÇİMİ -->
    <div id="ekran_alan" class="ekran">
        <div class="satir" style="margin-bottom:10px;">
            <button onclick="ekranGec('ekran_kur')" style="background:#fff; border:none; width:40px; height:40px; border-radius:50%; font-size:20px;">‹</button>
            <div style="background:#fff; flex:1; margin-left:10px; padding:10px 16px; border-radius:20px; font-weight:600;">Play Zone (Haritaya Dokun)</div>
        </div>

        <div style="position:relative;">
            <div id="harita_secim"></div>
            <button class="harita-odak-btn" onclick="secimKonumaOdakla()">🎯</button>
        </div>

        <div class="kart" style="margin-top:-16px; z-index:2;">
            <div class="satir">
                <div>
                    <div style="font-weight:800; font-size:18px;">Zone Radius</div>
                    <div id="yaricap_bilgi" style="font-size:13px; color:#666;">500 m • Avlanma Alanı</div>
                </div>
            </div>
            <input type="range" id="rng_yaricap" min="200" max="2000" step="100" value="500" style="width:100%; margin:16px 0; accent-color:#f97316;" oninput="yaricapGuncelle(this.value)">
            <button class="btn-turuncu" onclick="odaOlustur()">Apply & Create Lobby</button>
        </div>
    </div>

    <!-- 4. EKRAN: LOBİ -->
    <div id="ekran_lobi" class="ekran">
        <div class="satir" style="margin-bottom:15px;">
            <button onclick="ekranGec('ekran_home')" style="background:none; border:none; font-size:22px;">‹</button>
            <span style="font-weight:800; font-size:18px;">Hunting Lobby</span>
            <button onclick="navigator.clipboard.writeText(aktifKod); alert('Oda kodu kopyalandı: '+aktifKod)" style="background:#f97316; color:#fff; border:none; padding:6px 12px; border-radius:12px; font-weight:bold; font-size:12px;">Invite ↗</button>
        </div>

        <div class="kart" style="text-align:center; background:#fff7ed; border-color:#fed7aa;">
            <div style="font-size:12px; color:#c2410c; font-weight:700;">ROOM CODE</div>
            <div id="lobi_oda_kodu" style="font-size:32px; font-weight:900; letter-spacing:4px; color:#c2410c; margin:4px 0;">--.--</div>
        </div>

        <div style="display:flex; gap:10px; margin-bottom:12px;">
            <div class="kart" style="flex:1; margin:0; background:#fff1f2; border-color:#fecdd3;">
                <div style="font-size:12px; font-weight:800; color:#be123c;">🔴 CHASERS (Avcılar)</div>
                <div id="chaser_liste" style="font-size:13px; margin-top:6px; color:#444;">Yükleniyor...</div>
            </div>
            <div class="kart" style="flex:1; margin:0; background:#f0fdf4; border-color:#bbf7d0;">
                <div style="font-size:12px; font-weight:800; color:#15803d;">🟢 RUNNERS (Kaçanlar)</div>
                <div id="runner_liste" style="font-size:13px; margin-top:6px; color:#444;">Yükleniyor...</div>
            </div>
        </div>

        <button class="btn-beyaz" style="margin-bottom:8px;" onclick="rolDegistir()">Rolünü Değiştir (Chaser / Runner)</button>
        <button id="btn_oyunu_baslat" class="btn-turuncu" onclick="oyunuBaslat()">START HUNT</button>
    </div>

    <!-- 5. EKRAN: AKTİF OYUN & HARİTA -->
    <div id="ekran_oyun" class="ekran" style="padding:12px;">
        <div class="kart" style="margin-bottom:8px; padding:12px 16px;">
            <div class="satir">
                <div><div style="font-size:11px; color:#888;">Kalan Süre</div><div id="oyun_kalan_sure" style="font-size:24px; font-weight:900;">60:00</div></div>
                <div style="text-align:center;"><div style="font-size:11px; color:#888;">Kalan Runner</div><div id="oyun_kalan_kisi" style="font-size:22px; font-weight:900;">3/4</div></div>
                <div style="text-align:right;"><div style="font-size:11px; color:#888;">Rolün</div><div id="oyun_rol_etiket" style="font-size:18px; font-weight:900; color:#f97316;">RUNNER</div></div>
            </div>
        </div>

        <div style="position:relative; flex:1;">
            <div id="oyun_harita"></div>
            <button class="harita-odak-btn" onclick="oyunKonumaOdakla()">🎯</button>
        </div>

        <div class="kart" style="margin-top:8px; padding:10px; background:#fff7ed; border-color:#fed7aa; text-align:center;">
            <div id="konum_guncelleme_bilgi" style="font-size:12px; font-weight:700; color:#c2410c;">Konum güncellemesine kalan: 02:00</div>
        </div>

        <div style="display:flex; gap:8px; margin-top:8px;">
            <button class="btn-turuncu" style="flex:1; padding:14px; background:#111; box-shadow:none;" onclick="yakalandimBildir()">🏁 Yakalandım / Teslim Ol</button>
            <button class="btn-turuncu" style="flex:1; padding:14px;" onclick="cepModuAc()">🌙 Gizli Mod (Cep)</button>
        </div>
    </div>

    <!-- 6. EKRAN: OYUN BİTTİ & PROVİZYON -->
    <div id="ekran_bitti" class="ekran" style="background:#0f0f0f; color:#fff; text-align:center;">
        <div style="margin-top:30px; font-size:60px;">🏆</div>
        <div id="bitti_baslik" style="font-size:32px; font-weight:900; margin:10px 0;">HUNT COMPLETED!</div>
        <p id="bitti_aciklama" style="color:#aaa; font-size:14px;">Av sona erdi, kazananlar belli oldu.</p>

        <div style="text-align:left; font-size:13px; font-weight:800; color:#888; margin:15px 0 8px 0;">MAÇ SKORLARI & XP</div>
        <div id="bitti_siralama" style="flex:1; overflow-y:auto; margin-bottom:14px;"></div>

        <button class="btn-turuncu" onclick="tekrarOyna()">🔄 Tekrar Oyna (Lobiye Dön)</button>
        <button class="btn-beyaz" style="background:#222; color:#fff; border-color:#333; margin-top:8px;" onclick="ekranGec('ekran_home')">Ana Menü</button>
    </div>

    <!-- 7. EKRAN: PROFİL & GEÇMİŞ -->
    <div id="ekran_profil" class="ekran">
        <div class="satir" style="margin-bottom:15px;">
            <button onclick="ekranGec('ekran_home')" style="background:none; border:none; font-size:24px; cursor:pointer;">‹</button>
            <span style="font-weight:800; font-size:18px;">Profile & Stats</span>
            <span style="width:24px;"></span>
        </div>

        <div class="kart satir">
            <div>
                <div style="font-size:18px; font-weight:900;">Musti</div>
                <div style="font-size:12px; color:#666;">Level 6 • Scout</div>
            </div>
            <div style="background:#ffedd5; color:#c2410c; padding:6px 12px; border-radius:12px; font-weight:900;">295 Coins</div>
        </div>

        <div class="kart satir">
            <div style="text-align:center; flex:1;">
                <div style="font-size:12px; color:#666;">Chaser</div>
                <div style="font-size:20px; font-weight:900;">0 games</div>
            </div>
            <div style="border-left:1px solid #eee; text-align:center; flex:1;">
                <div style="font-size:12px; color:#666;">Runner</div>
                <div style="font-size:20px; font-weight:900; color:#f97316;">4 games</div>
            </div>
        </div>

        <div class="kart">
            <div style="font-weight:800; margin-bottom:10px;">Recent Games</div>
            <div style="font-size:13px; padding:8px 0; border-bottom:1px solid #eee; display:flex; justify-content:space-between;">
                <span><b>Won</b> • Manhunt (Runner)</span>
                <span style="color:#16a34a; font-weight:800;">+260 XP</span>
            </div>
            <div style="font-size:13px; padding:8px 0; display:flex; justify-content:space-between;">
                <span><b>Lost</b> • Manhunt (Runner)</span>
                <span style="color:#dc2626; font-weight:800;">+260 XP</span>
            </div>
        </div>
        <button class="btn-turuncu" onclick="ekranGec('ekran_home')">Geri Dön</button>
    </div>

</div>

<script>
let ayarlar = { sure: 60, konum: 2, yaricap: 500 };
let oyuncuAdi = "Musti", aktifKod = "", rol="RUNNER", lat = 41.2867, lon = 36.3300;
let haritaSecim = null, secimDaire = null, secimMarker = null;
let oyunHarita = null, oyunDaire = null, icDaire = null, oyuncuMarker = null, chaserPinleri = [];
let takipTimer = null, gpsIzleyici = null, uykuKilidi = null, sonTiklama = 0;
let oncekiFaz = "";

const HARITA_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

const oyuncuIkon = L.divIcon({
    className: '',
    html: '<div class="oyuncu-radar"><div class="oyuncu-dalga"></div><div class="oyuncu-merkez"></div></div>',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
});

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
}

function sesHazirla() {}

async function ekranAcikTut() {
    try {
        if ('wakeLock' in navigator && !uykuKilidi) {
            uykuKilidi = await navigator.wakeLock.request('screen');
        }
    } catch (e) {}
}

function cepModuAc() {
    ekranAcikTut();
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

window.addEventListener('load', () => {
    gpsBaslat();
});

function gpsBaslat() {
    ekranAcikTut();
    if (!navigator.geolocation) return;
    if (gpsIzleyici !== null) navigator.geolocation.clearWatch(gpsIzleyici);

    gpsIzleyici = navigator.geolocation.watchPosition(pos => {
        lat = pos.coords.latitude;
        lon = pos.coords.longitude;
        if (oyunHarita && oyuncuMarker) {
            oyuncuMarker.setLatLng([lat, lon]);
        }
    }, () => {}, { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 });
}

function ekranGec(id) {
    document.querySelectorAll('.ekran').forEach(e => e.classList.remove('aktif'));
    document.getElementById(id).classList.add('aktif');
    if(id === 'ekran_alan') setTimeout(haritaSecimKur, 150);
    if(id === 'ekran_oyun') setTimeout(oyunHaritaKur, 150);
}

function ayarSec(tip, deger, btn) {
    ayarlar[tip] = deger;
    btn.parentElement.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('secili'));
    btn.classList.add('secili');
}

function kodIlerle(suan, sonrakiId) {
    if (suan.value.length >= 1) {
        document.getElementById(sonrakiId).focus();
    }
}

function haritaSecimKur() {
    if(!haritaSecim) {
        haritaSecim = L.map('harita_secim', {zoomControl: false}).setView([lat, lon], 15);
        L.tileLayer(HARITA_URL, {maxZoom: 19, attribution: '© OpenStreetMap'}).addTo(haritaSecim);
        secimDaire = L.circle([lat, lon], {radius: ayarlar.yaricap, color: '#f97316', fillColor: '#fb923c', fillOpacity: 0.2}).addTo(haritaSecim);
        secimMarker = L.marker([lat, lon], {icon: oyuncuIkon}).addTo(haritaSecim);
        haritaSecim.on('click', e => {
            lat = e.latlng.lat; lon = e.latlng.lng;
            secimDaire.setLatLng(e.latlng);
            secimMarker.setLatLng(e.latlng);
        });
    }
    setTimeout(() => haritaSecim.invalidateSize(), 150);
}

function secimKonumaOdakla() {
    if(haritaSecim) haritaSecim.flyTo([lat, lon], 16);
}

function oyunKonumaOdakla() {
    if(oyunHarita) oyunHarita.flyTo([lat, lon], 16);
}

function yaricapGuncelle(val) {
    ayarlar.yaricap = parseInt(val);
    document.getElementById('yaricap_bilgi').innerText = `${val} m • Avlanma Alanı`;
    if(secimDaire) secimDaire.setRadius(ayarlar.yaricap);
}

async function odaOlustur() {
    ayarlar.kurucu = oyuncuAdi;
    ayarlar.merkez_lat = lat;
    ayarlar.merkez_lon = lon;
    let res = await fetch('/oda_kur', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(ayarlar)});
    let d = await res.json();
    aktifKod = d.kod;
    document.getElementById('lobi_oda_kodu').innerText = aktifKod;
    lobiAc();
}

async function odayaKatil() {
    let kod = "";
    for(let i=1; i<=5; i++) kod += document.getElementById('k'+i).value;
    if(kod.length !== 5) return;
    aktifKod = kod;

    let res = await fetch('/katil', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi})});
    let d = await res.json();
    if(d.hata) { alert(d.hata); return; }
    document.getElementById('lobi_oda_kodu').innerText = aktifKod;
    gpsBaslat();
    lobiAc();
}

function lobiAc() {
    ekranGec('ekran_lobi');
    if(takipTimer) clearInterval(takipTimer);
    takipTimer = setInterval(sunucuDurumCek, 1000);
}

async function rolDegistir() {
    rol = (rol === "RUNNER") ? "CHASER" : "RUNNER";
    await fetch('/rol_degis', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi, rol:rol})});
}

async function oyunuBaslat() {
    await fetch('/baslat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod})});
}

async function tekrarOyna() {
    await fetch('/tekrar_oyna', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod})});
    oncekiFaz = "";
    ekranGec('ekran_lobi');
}

function oyunHaritaKur() {
    if(!oyunHarita) {
        oyunHarita = L.map('oyun_harita', {zoomControl: false}).setView([lat, lon], 15);
        L.tileLayer(HARITA_URL, {maxZoom: 19, attribution: '© OpenStreetMap'}).addTo(oyunHarita);
        oyunDaire = L.circle([lat, lon], {radius: ayarlar.yaricap, color: '#f97316', fillColor: '#fb923c', fillOpacity: 0.15}).addTo(oyunHarita);
        icDaire = L.circle([lat, lon], {radius: ayarlar.yaricap * 0.75, color: '#333', dashArray: '6, 6', fill: false}).addTo(oyunHarita);
        oyuncuMarker = L.marker([lat, lon], {icon: oyuncuIkon, zIndexOffset: 1000}).addTo(oyunHarita);
    }
    setTimeout(() => oyunHarita.invalidateSize(), 150);
}

async function yakalandimBildir() {
    if(confirm("Avcı tarafından yakalandığını onaylıyor musun?")) {
        await fetch('/yakalandim', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi})});
    }
}

async function sunucuDurumCek() {
    if(!aktifKod) return;
    let res = await fetch('/durum', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kod:aktifKod, oyuncu:oyuncuAdi, lat:lat, lon:lon})});
    let d = await res.json();
    if(d.hata) return;

    if(!d.basladi) {
        if(document.getElementById('ekran_bitti').classList.contains('aktif')) ekranGec('ekran_lobi');
        let chasers = [], runners = [];
        for(let isim in d.oyuncular) {
            if(d.oyuncular[isim].rol === "CHASER") chasers.push(isim);
            else runners.push(isim);
        }
        document.getElementById('chaser_liste').innerHTML = chasers.join('<br>') || "Henüz yok";
        document.getElementById('runner_liste').innerHTML = runners.join('<br>') || "Henüz yok";
    } else {
        let ben = d.oyuncular[oyuncuAdi];
        if(!ben) return;
        rol = ben.rol;

        if (oncekiFaz !== "BITTI" && d.faz === "BITTI") {
            document.getElementById('cep_modu_katman').style.display = 'none';
        }
        oncekiFaz = d.faz;

        if(d.faz === "BITTI") {
            if(!document.getElementById('ekran_bitti').classList.contains('aktif')) ekranGec('ekran_bitti');
            document.getElementById('bitti_baslik').innerText = d.kazanan_baslik;
            document.getElementById('bitti_aciklama').innerText = d.kazanan_aciklama;

            let sirali = Object.entries(d.oyuncular).sort((a, b) => b[1].xp - a[1].xp);
            let siraHtml = "";
            sirali.forEach((item, idx) => {
                let isim = item[0], p = item[1];
                siraHtml += `<div style="background:#1a1a1a; border:1px solid #2a2a2a; border-radius:14px; padding:12px 16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <div><b>#${idx+1} ${isim}</b> (${p.rol})</div>
                    <div style="color:#f97316; font-weight:900;">${p.xp} XP</div>
                </div>`;
            });
            document.getElementById('bitti_siralama_liste').innerHTML = siraHtml;
        } else {
            if(document.getElementById('ekran_lobi').classList.contains('aktif')) ekranGec('ekran_oyun');
            document.getElementById('oyun_kalan_sure').innerText = d.oyun_sayac;
            document.getElementById('oyun_kalan_kisi').innerText = `${d.kalan_runner}/${d.toplam_runner}`;
            document.getElementById('oyun_rol_etiket').innerText = rol;
            document.getElementById('konum_guncelleme_bilgi').innerText = `Sonraki konum bildirimi: ${d.konum_sayac}`;

            if(oyunHarita) {
                oyunDaire.setLatLng([d.merkez_lat, d.merkez_lon]);
                oyunDaire.setRadius(d.aktif_alan);
                icDaire.setLatLng([d.merkez_lat, d.merkez_lon]);
                oyuncuMarker.setLatLng([lat, lon]);

                chaserPinleri.forEach(p => oyunHarita.removeLayer(p));
                chaserPinleri = [];
                if(rol === "CHASER") {
                    d.bildirilen_pinler.forEach(pin => {
                        let hIkon = L.divIcon({
                            className: '',
                            html: `<div class="hedef-pin"><div class="hedef-etiket">${pin.isim}</div><div class="hedef-dalga"></div><div class="hedef-merkez"></div></div>`,
                            iconSize: [26, 26], iconAnchor: [13, 13]
                        });
                        let m = L.marker([pin.lat, pin.lon], {icon: hIkon}).addTo(oyunHarita);
                        chaserPinleri.push(m);
                    });
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
        "name": "Hunting Game", "short_name": "Hunt", "start_url": "/", "display": "standalone",
        "background_color": "#f8f9fa", "theme_color": "#f97316",
        "icons": [{"src": "https://img.icons8.com/ios-filled/512/ffffff/marker.png", "sizes": "512x512", "type": "image/png"}]
    })

@app.route('/sw.js')
def service_worker():
    return "self.addEventListener('fetch', function(event) {});", 200, {'Content-Type': 'application/javascript'}

@app.route('/oda_kur', methods=['POST'])
def oda_kur():
    v = request.json
    kod = ''.join(random.choices("0123456789", k=5))
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
        "oyuncular": {
            v["kurucu"]: {"rol": "RUNNER", "lat": v.get("merkez_lat", 41.2867), "lon": v.get("merkez_lon", 36.3300), "xp": 1220, "yakalandi": False}
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
    oda["oyuncular"][v["oyuncu"]] = {"rol": "RUNNER", "lat": oda["merkez_lat"], "lon": oda["merkez_lon"], "xp": 1000, "yakalandi": False}
    return jsonify({"basari": True})

@app.route('/rol_degis', methods=['POST'])
def rol_degis():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if oda and v["oyuncu"] in oda["oyuncular"]:
        oda["oyuncular"][v["oyuncu"]]["rol"] = v.get("rol")
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
    for p in oda["oyuncular"].values():
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
        for p in oda["oyuncular"].values():
            p["yakalandi"] = False
    return jsonify({"basari": True})

@app.route('/yakalandim', methods=['POST'])
def yakalandim():
    v = request.json
    oda = odalar.get(v.get("kod"))
    if oda and v["oyuncu"] in oda["oyuncular"]:
        oda["oyuncular"][v["oyuncu"]]["yakalandi"] = True
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

    if not oda["basladi"]:
        return jsonify({"basladi": False, "oyuncular": oda["oyuncular"], "ayarlar": oda["ayarlar"]})

    gecen = int(time.time() - oda["baslangic"])
    toplam_sure_sn = int(oda["ayarlar"]["sure"] * 60)
    oyun_kalan = toplam_sure_sn - gecen

    toplam_runner = 0
    kalan_runner = 0
    for isim, p in oda["oyuncular"].items():
        if p["rol"] == "RUNNER":
            toplam_runner += 1
            if not p["yakalandi"]:
                kalan_runner += 1

    if oyun_kalan <= 0 or (toplam_runner > 0 and kalan_runner == 0):
        if kalan_runner == 0 and toplam_runner > 0:
            kazanan_baslik = "CHASERS WON!"
            kazanan_aciklama = "Tüm Runner oyuncuları süre bitmeden yakalandı!"
            if not oda.get("odul_verildi"):
                for p in oda["oyuncular"].values():
                    if p["rol"] == "CHASER": p["xp"] += 300
                oda["odul_verildi"] = True
        else:
            kazanan_baslik = "RUNNERS WON!"
            kazanan_aciklama = f"Süre doldu ve {kalan_runner} kaçan hayatta kaldı!"
            if not oda.get("odul_verildi"):
                for p in oda["oyuncular"].values():
                    if p["rol"] == "RUNNER" and not p["yakalandi"]: p["xp"] += 350
                oda["odul_verildi"] = True

        return jsonify({
            "basladi": True, "faz": "BITTI", "kazanan_baslik": kazanan_baslik,
            "kazanan_aciklama": kazanan_aciklama, "oyuncular": oda["oyuncular"]
        })

    konum_periyot_sn = int(oda["ayarlar"]["konum"] * 60)
    konum_kalan = konum_periyot_sn - (gecen % konum_periyot_sn)

    periyot_no = gecen // konum_periyot_sn
    if periyot_no > oda["son_periyot"]:
        oda["son_periyot"] = periyot_no
        pinler = []
        for isim, p in oda["oyuncular"].items():
            if p["rol"] == "RUNNER" and not p["yakalandi"]:
                pinler.append({"isim": isim, "lat": p["lat"], "lon": p["lon"]})
        oda["bildirilen_pinler"] = pinler

    return jsonify({
        "basladi": True, "faz": "OYUN",
        "oyun_sayac": sure_formatla(oyun_kalan),
        "konum_sayac": sure_formatla(konum_kalan),
        "aktif_alan": oda["ayarlar"]["yaricap"],
        "merkez_lat": oda["merkez_lat"], "merkez_lon": oda["merkez_lon"],
        "toplam_runner": max(1, toplam_runner), "kalan_runner": kalan_runner,
        "bildirilen_pinler": oda["bildirilen_pinler"],
        "oyuncular": oda["oyuncular"], "ayarlar": oda["ayarlar"]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
