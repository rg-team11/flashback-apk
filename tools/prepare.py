#!/usr/bin/env python3
"""Sastavlja Android projekat: SDL2 android-project + REminiscence izvorni kod + zakrpe.
Upotreba: prepare.py <sdl_dir> <rem_dir> <out_dir>"""
import os, re, shutil, sys

sdl, rem, out, stb = sys.argv[1:5]

def rd(p):
    with open(p, encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()

def wr(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(s)

def sub(s, old, new, count=1):
    n = s.count(old)
    assert n >= 1, "ne nalazim u kodu: %r" % old[:60]
    if count == 1:
        assert n == 1, "vise pojavljivanja (%d): %r" % (n, old[:60])
    return s.replace(old, new)

# 1) SDL android-project kao osnova
if os.path.exists(out):
    shutil.rmtree(out)
shutil.copytree(os.path.join(sdl, "android-project"), out)
jni = os.path.join(out, "app", "jni")
os.makedirs(os.path.join(jni, "SDL"))
for n in ("include", "src"):
    shutil.copytree(os.path.join(sdl, n), os.path.join(jni, "SDL", n))
shutil.copy(os.path.join(sdl, "Android.mk"), os.path.join(jni, "SDL", "Android.mk"))
os.remove(os.path.join(jni, "CMakeLists.txt")) if os.path.exists(os.path.join(jni, "CMakeLists.txt")) else None

# 2) izvorni kod igre
srcdir = os.path.join(jni, "src")
shutil.rmtree(srcdir)
os.makedirs(srcdir)
files = """collision cpc_player cutscene decode_mac file fs game graphics main menu midi_parser mixer
mod_player ogg_player piege prf_player protection resource resource_aba resource_mac resource_paq
scaler screenshot seq_player sfx_player staticres systemstub_sdl unpack util video""".split()
for f in os.listdir(rem):
    if f.endswith((".cpp", ".h")):
        shutil.copy(os.path.join(rem, f), os.path.join(srcdir, f))

shutil.copy(os.path.join(stb, "stb_vorbis.c"), os.path.join(srcdir, "stb_vorbis.c"))

wr(os.path.join(srcdir, "Android.mk"), """LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := main
LOCAL_C_INCLUDES := $(LOCAL_PATH)/../SDL/include
LOCAL_CPPFLAGS := -std=gnu++11 -DUSE_ZLIB -DUSE_STB_VORBIS -fexceptions -Wno-narrowing -Wno-write-strings
LOCAL_CFLAGS := -O2
LOCAL_SRC_FILES := %s
LOCAL_SHARED_LIBRARIES := SDL2
LOCAL_LDLIBS := -lz -llog
include $(BUILD_SHARED_LIBRARY)
""" % " \\\n    ".join(f + ".cpp" for f in files))

wr(os.path.join(jni, "Application.mk"), """APP_ABI := armeabi-v7a arm64-v8a
APP_PLATFORM := android-21
APP_STL := c++_static
""")

# 3) zakrpa main.cpp
p = os.path.join(srcdir, "main.cpp")
s = rd(p)
helper = r'''
#ifdef __ANDROID__
static char g_androidMsg[1500];
static const char *androidFindDataPath() {
	static char ext[600];
	const char *candidates[6];
	int n = 0;
	candidates[n++] = "/sdcard/REminiscence/DATA";
	candidates[n++] = "/storage/emulated/0/REminiscence/DATA";
	const char *ep = SDL_AndroidGetExternalStoragePath();
	if (ep) {
		snprintf(ext, sizeof(ext), "%s/DATA", ep);
		candidates[n++] = ext;
	}
	candidates[n++] = "/sdcard/Android/media/org.libsdl.app/DATA";
	snprintf(g_androidMsg, sizeof(g_androidMsg), "Nisu pronadjeni fajlovi igre.\n\nStavi ih u folder:\n/sdcard/REminiscence/DATA\n\n(za Macintosh: FLASHBACK.BIN ili FLASHBACK.RSRC i ostali fajlovi iz DATA)\n\nProveravao sam:\n");
	for (int i = 0; i < n; ++i) {
		struct stat st;
		if (stat(candidates[i], &st) == 0 && S_ISDIR(st.st_mode)) {
			return candidates[i];
		}
		size_t l = strlen(g_androidMsg);
		snprintf(g_androidMsg + l, sizeof(g_androidMsg) - l, "%s\n", candidates[i]);
	}
	return 0;
}
#endif

#ifdef __ANDROID__
static int re_main(int argc, char *argv[]);
int main(int argc, char *argv[]) {
	int r = re_main(argc, argv);
	fflush(NULL);
	exit(r); // ubij proces da svako sledece pokretanje krene cisto
}
static int re_main(int argc, char *argv[]) {
#else
int main(int argc, char *argv[]) {
#endif'''
s = sub(s, "\nint main(int argc, char *argv[]) {", helper)
s = sub(s, '\tg_debugMask = 0;', '''#ifdef __ANDROID__
	{
		const char *dp = androidFindDataPath();
		for (int tries = 0; !dp && tries < 60; ++tries) { // sacekaj dozvolu za pristup memoriji
			SDL_Delay(500);
			dp = androidFindDataPath();
		}
		if (dp) {
			dataPath = dp;
		}
		const char *ip = SDL_AndroidGetInternalStoragePath();
		if (ip) {
			savePath = ip;
		}
		argc = 1;
	}
#endif
	g_debugMask = 0;''')
s = sub(s, '\t\tconst int c = getopt_long(argc, argv, "", options, &index);',
'''#ifdef __ANDROID__
		(void)options; (void)index;
		const int c = -1;
#else
		const int c = getopt_long(argc, argv, "", options, &index);
#endif''')
s = sub(s, '''		error("Unable to find data files, check that all required files are present");''',
'''		error("Unable to find data files, check that all required files are present");
#ifdef __ANDROID__
		SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "REminiscence", g_androidMsg, NULL);
#endif''')
wr(p, s)

# 4) zakrpa tastera (Back -> Escape, Shift i inventar na tastere daljinskog)
p = os.path.join(srcdir, "systemstub_sdl.cpp")
s = rd(p)
s = sub(s, "\t\tcase SDLK_ESCAPE:\n", "\t\tcase SDLK_AC_BACK:\n\t\tcase SDLK_ESCAPE:\n", count=0)
s = sub(s, "\t\tcase SDLK_LSHIFT:\n\t\t\t_pi.shift", "\t\tcase SDLK_LSHIFT:\n\t\tcase SDLK_MENU:\n\t\tcase SDLK_PAGEUP:\n\t\t\t_pi.shift", count=0)
s = sub(s, "\t\tcase SDLK_RETURN:\n\t\t\t_pi.enter", "\t\tcase SDLK_RETURN:\n\t\tcase SDLK_SELECT:\n\t\tcase SDLK_KP_ENTER:\n\t\t\t_pi.enter", count=0)
s = sub(s, "\t\tcase SDLK_TAB:\n", "\t\tcase SDLK_TAB:\n\t\tcase SDLK_PAGEDOWN:\n", count=0)
wr(p, s)

# 4b) dzojped: otvori sve uredjaje, logovanje dugmadi, dodatni tasteri
s = sub(s, """		SDL_GameControllerAddMappingsFromFile("gamecontrollerdb.txt");
		if (SDL_IsGameController(kJoystickIndex)) {
			_controller = SDL_GameControllerOpen(kJoystickIndex);
		}
		if (!_controller) {
			_joystick = SDL_JoystickOpen(kJoystickIndex);
		}
""", """		SDL_GameControllerAddMappingsFromFile("gamecontrollerdb.txt");
		for (int i = 0; i < SDL_NumJoysticks(); ++i) {
			info("Input device %d: '%s' gamecontroller=%d", i, SDL_JoystickNameForIndex(i), (int)SDL_IsGameController(i));
		}
		for (int i = 0; i < SDL_NumJoysticks(); ++i) {
			if (SDL_IsGameController(i)) {
				SDL_GameController *c = SDL_GameControllerOpen(i);
				if (c && !_controller) {
					_controller = c;
				}
			}
		}
		if (!_controller) {
			for (int i = 0; i < SDL_NumJoysticks(); ++i) {
				SDL_Joystick *j = SDL_JoystickOpen(i);
				if (j && !_joystick) {
					_joystick = j;
				}
			}
		}
""")
s = sub(s, """			const bool pressed = (ev.jbutton.state == SDL_PRESSED);
			switch (ev.jbutton.button) {
""", """			const bool pressed = (ev.jbutton.state == SDL_PRESSED);
			info("joystick button %d pressed=%d", (int)ev.jbutton.button, (int)pressed);
			switch (ev.jbutton.button) {
			case 4:
				_pi.shift = pressed;
				break;
			case 5:
				_pi.backspace = pressed;
				break;
			case 6:
			case 7:
			case 8:
			case 9:
				_pi.escape = pressed;
				break;
""")
s = sub(s, """			const bool pressed = (ev.cbutton.state == SDL_PRESSED);
			switch (ev.cbutton.button) {
""", """			const bool pressed = (ev.cbutton.state == SDL_PRESSED);
			info("controller button %d pressed=%d", (int)ev.cbutton.button, (int)pressed);
			switch (ev.cbutton.button) {
			case SDL_CONTROLLER_BUTTON_LEFTSHOULDER:
				_pi.shift = pressed;
				break;
			case SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:
				_pi.backspace = pressed;
				break;
""")
wr(p, s)

# 4c) mod plejer: tempo 0 (Mac verzija) izaziva beskonacnu petlju u mix() -> zamrzavanje
p = os.path.join(srcdir, "mod_player.cpp")
s = rd(p)
s = sub(s, "_impl->_songTempo = tempo;", "_impl->_songTempo = (tempo > 0) ? tempo : 125;")
s = sub(s, "const int samplesPerTick = _mixingRate / (50 * _songTempo / BASE_TEMPO);",
        "int samplesPerTick = _mixingRate / (50 * (_songTempo > 0 ? _songTempo : BASE_TEMPO) / BASE_TEMPO);\n\t\tif (samplesPerTick < 1) {\n\t\t\tsamplesPerTick = 1;\n\t\t}")
wr(p, s)

# 4d) bez paletnog fade-out efekta (prikazivao je zaostalu sliku jarkim bojama)
p = os.path.join(srcdir, "main.cpp")
s = rd(p)
s = sub(s, "g_options.fade_out_palette = true;", "g_options.fade_out_palette = false;")
wr(p, s)

p = os.path.join(srcdir, "video.cpp")
s = rd(p)
s = sub(s, """	} else {
		_stub->fadeScreen();
	}
}""", """	} else {
		// kao originalni fade-out: paleta ostaje crna (ali bez iscrtavanja stare slike)
		for (int c = 0; c < 256; ++c) {
			Color col;
			col.r = col.g = col.b = 0;
			_stub->setPaletteEntry(c, &col);
		}
		_stub->fadeScreen();
	}
}""")
wr(p, s)

# 5) Java aktivnost (trazi dozvolu za citanje memorije)
wr(os.path.join(out, "app/src/main/java/org/libsdl/app/REActivity.java"), """package org.libsdl.app;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;

public class REActivity extends SDLActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        if (Build.VERSION.SDK_INT >= 23) {
            try {
                if (checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                    requestPermissions(new String[] { Manifest.permission.READ_EXTERNAL_STORAGE }, 1);
                }
            } catch (Exception e) {
            }
        }
        super.onCreate(savedInstanceState);
    }
}
""")

# 6) manifest, gradle, ime aplikacije
p = os.path.join(out, "app/src/main/AndroidManifest.xml")
s = rd(p)
s = sub(s, '<activity android:name="SDLActivity"', '<activity android:name="REActivity"')
s = sub(s, '<category android:name="android.intent.category.LAUNCHER" />',
        '<category android:name="android.intent.category.LAUNCHER" />\n                <category android:name="android.intent.category.LEANBACK_LAUNCHER" />')
s = sub(s, '<uses-permission android:name="android.permission.VIBRATE" />',
        '<uses-permission android:name="android.permission.VIBRATE" />\n    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />\n    <uses-feature android:name="android.software.leanback" android:required="false" />')
s = sub(s, 'android:allowBackup="true"', 'android:allowBackup="true"\n        android:requestLegacyExternalStorage="true"\n        android:banner="@mipmap/ic_launcher"')
wr(p, s)

p = os.path.join(out, "app/build.gradle")
s = rd(p)
s = sub(s, "minSdkVersion 19", "minSdkVersion 21")
s = sub(s, "targetSdkVersion 34", "targetSdkVersion 28")
s = sub(s, 'arguments "APP_PLATFORM=android-19"', 'arguments "APP_PLATFORM=android-21"')
s = sub(s, "abiFilters 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'", "abiFilters 'armeabi-v7a', 'arm64-v8a'", count=0)
wr(p, s)

wr(os.path.join(out, "app/src/main/res/values/strings.xml"),
   '<resources>\n    <string name="app_name">Flashback</string>\n</resources>\n')

# 7) ikonica i TV baner (opciono): ako u repozitorijumu postoji icon.png
icon_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.png")
if os.path.exists(icon_src):
    from PIL import Image
    im = Image.open(icon_src).convert("RGBA")
    w, h = im.size
    side = min(w, h)
    sq = im.crop(((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side))
    for d, sz in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        sq.resize((sz, sz), Image.LANCZOS).save(os.path.join(out, "app/src/main/res/mipmap-%s/ic_launcher.png" % d))
    # TV baner 320x180: slika u celini na crnoj pozadini
    ban = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
    r = min(320 / w, 180 / h)
    nw, nh = int(w * r), int(h * r)
    ban.paste(im.resize((nw, nh), Image.LANCZOS), ((320 - nw) // 2, (180 - nh) // 2))
    ban.convert("RGB").save(os.path.join(out, "app/src/main/res/mipmap-xhdpi/banner.png"))
    mp = os.path.join(out, "app/src/main/AndroidManifest.xml")
    ms = rd(mp)
    wr(mp, sub(ms, 'android:banner="@mipmap/ic_launcher"', 'android:banner="@mipmap/banner"'))
    print("ikonica postavljena iz icon.png")

print("OK: projekat sastavljen u", out)
