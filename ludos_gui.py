import os, json, secrets, string, time, webbrowser, textwrap, threading
from datetime import datetime, timedelta
import customtkinter as ctk

try:
    import pyotp
except:
    pyotp = None
try:
    import keyring
except:
    keyring = None

APP = "ludos-gui"
HOME = os.path.expanduser("~")
INDEX_PATH = os.path.join(HOME, ".ludos_totp_index.json")
ROTATION_FILE = os.path.join(HOME, ".ludos_rotation.txt")

DATA_BROKERS = {
    "whitepages": "https://www.whitepages.com/suppression_requests",
    "spokeo": "https://www.spokeo.com/optout",
    "beenverified": "https://www.beenverified.com/app/optout/search",
    "intelius": "https://www.intelius.com/opt-out/submit",
    "mylife": "https://www.mylife.com/ccpa",
    "radaris": "https://radaris.com/control/privacy",
    "truthfinder": "https://www.truthfinder.com/opt-out/",
    "fastpeople": "https://www.fastpeoplesearch.com/removal",
    "peoplefinder": "https://www.peoplefinder.com/optout",
    "peekyou": "https://www.peekyou.com/about/contact/optout/index.php",
    "usphonebook": "https://www.usphonebook.com/opt-out",
    "clustrmaps": "https://clustrmaps.com/bl/opt-out",
    "neighborwho": "https://www.neighborwho.com/optout/",
    "searchpeoplefree": "https://www.searchpeoplefree.com/opt-out",
    "zabasearch": "https://www.zabasearch.com/optOut.php"
}

REMOVAL_PORTALS = {
    "google_outdated": "https://search.google.com/search-console/remove-outdated-content",
    "google_personal": "https://support.google.com/websearch/troubleshooter/3111061",
    "bing_removal": "https://www.bing.com/webmaster/tools/content-removal"
}

ACCOUNT_PAGES = {
    "youtube_delete": "https://myaccount.google.com/deleteservices",
    "discord_delete": "https://support.discord.com/hc/en-us/articles/212500837-Deleting-Your-Account",
    "github_delete": "https://github.com/settings/admin",
    "vercel_delete": "https://vercel.com/docs/accounts/account-deletion",
    "twitter_delete": "https://help.x.com/en/managing-your-account/how-to-deactivate-twitter-account",
    "instagram_delete": "https://www.instagram.com/accounts/login/?next=/accounts/remove/request/permanent/",
    "facebook_delete": "https://www.facebook.com/help/delete_account"
}

def load_index():
    if not os.path.exists(INDEX_PATH):
        return {}
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_index(idx):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2)

def strong_password(length=24, use_upper=True, use_lower=True, use_digits=True, use_symbols=True):
    pools = []
    if use_upper: pools.append(string.ascii_uppercase)
    if use_lower: pools.append(string.ascii_lowercase)
    if use_digits: pools.append(string.digits)
    if use_symbols: pools.append("!@#$%^&*()-_=+[]{};:,<.>/?")
    pool = "".join(pools) if pools else string.ascii_letters + string.digits
    while True:
        chars = []
        for s in pools: chars.append(secrets.choice(s))
        chars += [secrets.choice(pool) for _ in range(max(0, length - len(chars)))]
        secrets.SystemRandom().shuffle(chars)
        pw = "".join(chars[:length])
        if not pools or all(any(c in pw for c in s) for s in pools): return pw

def dmca_letter(name, email, infringing_urls, original_desc, signature_name):
    body = f"""
To Whom It May Concern,

I am the copyright owner of the material identified below. I request removal or disabling of access to infringing content under 17 U.S.C. § 512(c).

Original work: {original_desc}
Infringing URLs:
{os.linesep.join(infringing_urls)}

My contact information:
Name: {name}
Email: {email}

I have a good-faith belief that the use of the material is not authorized by the copyright owner, its agent, or the law.
The information in this notice is accurate, and under penalty of perjury, I am authorized to act on behalf of the owner.

Signature: {signature_name}
Date: {datetime.utcnow().date().isoformat()}
"""
    return textwrap.dedent(body).strip()

def privacy_erasure_letter(name, email, identifiers, law):
    body = f"""
Hello,

I am exercising my right to deletion under {law}. Please delete all personal data related to me across your systems, including backups when feasible, and confirm completion.

Identifiers:
{os.linesep.join(identifiers)}

Contact:
Name: {name}
Email: {email}

Please confirm receipt and completion within the statutory period and describe any data you are legally required to retain.
"""
    return textwrap.dedent(body).strip()

class RotationWorker:
    def __init__(self):
        self.thread = None
        self.stop_event = threading.Event()
    def start(self, hours, length, opts):
        if self.thread and self.thread.is_alive(): return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run, args=(hours, length, opts), daemon=True)
        self.thread.start()
    def run(self, hours, length, opts):
        interval = max(0.1, float(hours)) * 3600
        while not self.stop_event.is_set():
            pw = strong_password(length, *opts)
            with open(ROTATION_FILE, "a", encoding="utf-8") as f:
                f.write(f"{datetime.utcnow().isoformat()}Z {pw}\n")
            for _ in range(int(interval)):
                if self.stop_event.is_set(): break
                time.sleep(1)
    def stop(self):
        self.stop_event.set()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("Ludos — Privacy Toolkit • Made by Polar")
        self.geometry("980x700")
        self.minsize(900, 640)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(self, text="Ludos — Legal Privacy Toolkit (Passwords • TOTP • Letters • Portals)", font=("Inter", 18, "bold"))
        header.grid(row=0, column=0, padx=16, pady=(16,8), sticky="w")

        self.tabs = ctk.CTkTabview(self, width=960, height=560, segmented_button_fg_color=None, segmented_button_selected_color=None)
        self.tabs.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")

        self.tab_pw = self.tabs.add("Passwords")
        self.tab_totp = self.tabs.add("TOTP")
        self.tab_letters = self.tabs.add("Takedown Letters")
        self.tab_portals = self.tabs.add("Removal Portals")

        self.rotation = RotationWorker()

        self.build_passwords()
        self.build_totp()
        self.build_letters()
        self.build_portals()

        legal = "This tool does not bypass security, alter provider logs, or delete third-party content you do not control. It provides strong passwords, TOTP codes for your own exported secrets, standard takedown letters, and quick links to official removal/account-closure pages. You are responsible for complying with laws and ToS."
        footer = ctk.CTkLabel(self, text=legal, wraplength=920, font=("Inter", 12))
        footer.grid(row=2, column=0, padx=16, pady=(8,16), sticky="we")

    def build_passwords(self):
        frame = self.tab_pw
        frame.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(frame, corner_radius=12)
        top.grid(row=0, column=0, padx=16, pady=16, sticky="we")
        top.grid_columnconfigure(6, weight=1)

        ctk.CTkLabel(top, text="Length").grid(row=0, column=0, padx=8, pady=8)
        self.pw_length = ctk.CTkSlider(top, from_=8, to=64, number_of_steps=56)
        self.pw_length.set(24)
        self.pw_length.grid(row=0, column=1, padx=8, pady=8, sticky="we")

        self.use_upper = ctk.CTkCheckBox(top, text="A-Z"); self.use_upper.select()
        self.use_lower = ctk.CTkCheckBox(top, text="a-z"); self.use_lower.select()
        self.use_digits = ctk.CTkCheckBox(top, text="0-9"); self.use_digits.select()
        self.use_symbols = ctk.CTkCheckBox(top, text="Symbols"); self.use_symbols.select()
        self.use_upper.grid(row=0, column=2, padx=6)
        self.use_lower.grid(row=0, column=3, padx=6)
        self.use_digits.grid(row=0, column=4, padx=6)
        self.use_symbols.grid(row=0, column=5, padx=6)

        self.pw_output = ctk.CTkEntry(frame, placeholder_text="Generated password will appear here", width=840)
        self.pw_output.grid(row=1, column=0, padx=16, pady=(0,8), sticky="we")

        btns = ctk.CTkFrame(frame, corner_radius=12)
        btns.grid(row=2, column=0, padx=16, pady=8, sticky="we")
        gen_btn = ctk.CTkButton(btns, text="Generate", command=self.generate_password, corner_radius=12)
        copy_btn = ctk.CTkButton(btns, text="Copy", command=self.copy_password, corner_radius=12)
        gen_btn.grid(row=0, column=0, padx=6, pady=8)
        copy_btn.grid(row=0, column=1, padx=6, pady=8)

        rot = ctk.CTkFrame(frame, corner_radius=12)
        rot.grid(row=3, column=0, padx=16, pady=8, sticky="we")
        ctk.CTkLabel(rot, text=f"Rotation log file: {ROTATION_FILE}").grid(row=0, column=0, columnspan=4, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(rot, text="Every (hours)").grid(row=1, column=0, padx=8, pady=6)
        self.rot_hours = ctk.CTkEntry(rot, width=100)
        self.rot_hours.insert(0, "2")
        self.rot_hours.grid(row=1, column=1, padx=8, pady=6)
        ctk.CTkLabel(rot, text="Length").grid(row=1, column=2, padx=8, pady=6)
        self.rot_len = ctk.CTkEntry(rot, width=80)
        self.rot_len.insert(0, "24")
        self.rot_len.grid(row=1, column=3, padx=8, pady=6)
        self.rot_upper = ctk.CTkCheckBox(rot, text="A-Z"); self.rot_upper.select()
        self.rot_lower = ctk.CTkCheckBox(rot, text="a-z"); self.rot_lower.select()
        self.rot_digits = ctk.CTkCheckBox(rot, text="0-9"); self.rot_digits.select()
        self.rot_symbols = ctk.CTkCheckBox(rot, text="Symbols"); self.rot_symbols.select()
        self.rot_upper.grid(row=2, column=0, padx=6, pady=6)
        self.rot_lower.grid(row=2, column=1, padx=6, pady=6)
        self.rot_digits.grid(row=2, column=2, padx=6, pady=6)
        self.rot_symbols.grid(row=2, column=3, padx=6, pady=6)
        start_btn = ctk.CTkButton(rot, text="Start Rotation", command=self.start_rotation, corner_radius=12)
        stop_btn = ctk.CTkButton(rot, text="Stop Rotation", command=self.stop_rotation, corner_radius=12)
        start_btn.grid(row=3, column=0, padx=8, pady=8)
        stop_btn.grid(row=3, column=1, padx=8, pady=8)

    def generate_password(self):
        length = int(self.pw_length.get())
        pw = strong_password(length, self.use_upper.get()==1, self.use_lower.get()==1, self.use_digits.get()==1, self.use_symbols.get()==1)
        self.pw_output.delete(0, "end")
        self.pw_output.insert(0, pw)

    def copy_password(self):
        pw = self.pw_output.get().strip()
        if pw:
            self.clipboard_clear()
            self.clipboard_append(pw)

    def start_rotation(self):
        try:
            hours = float(self.rot_hours.get().strip())
            length = int(self.rot_len.get().strip())
            opts = (self.rot_upper.get()==1, self.rot_lower.get()==1, self.rot_digits.get()==1, self.rot_symbols.get()==1)
            self.rotation.start(hours, length, opts)
        except:
            pass

    def stop_rotation(self):
        self.rotation.stop()

    def build_totp(self):
        frame = self.tab_totp
        frame.grid_columnconfigure(1, weight=1)

        warn = "TOTP works only if you legitimately export the Base32 secret from your own account."
        ctk.CTkLabel(frame, text=warn).grid(row=0, column=0, columnspan=3, padx=16, pady=(16,8), sticky="w")

        ctk.CTkLabel(frame, text="Label").grid(row=1, column=0, padx=16, pady=8, sticky="e")
        self.t_label = ctk.CTkEntry(frame, width=220)
        self.t_label.grid(row=1, column=1, padx=8, pady=8, sticky="we")
        ctk.CTkLabel(frame, text="Base32 Secret").grid(row=2, column=0, padx=16, pady=8, sticky="e")
        self.t_secret = ctk.CTkEntry(frame, width=360, show="•")
        self.t_secret.grid(row=2, column=1, padx=8, pady=8, sticky="we")

        add_btn = ctk.CTkButton(frame, text="Add/Update Secret", command=self.totp_add, corner_radius=12)
        add_btn.grid(row=3, column=1, padx=8, pady=8, sticky="w")

        self.t_codes = ctk.CTkTextbox(frame, height=240, corner_radius=12)
        self.t_codes.grid(row=4, column=0, columnspan=3, padx=16, pady=8, sticky="nsew")
        frame.grid_rowconfigure(4, weight=1)

        list_btn = ctk.CTkButton(frame, text="List Labels", command=self.totp_list, corner_radius=12)
        code_btn = ctk.CTkButton(frame, text="Get Code", command=self.totp_code, corner_radius=12)
        rem_btn = ctk.CTkButton(frame, text="Remove Label", command=self.totp_remove, corner_radius=12)
        self.t_code_label = ctk.CTkEntry(frame, placeholder_text="Label for code/remove", width=220)
        list_btn.grid(row=5, column=0, padx=16, pady=8, sticky="w")
        self.t_code_label.grid(row=5, column=1, padx=8, pady=8, sticky="w")
        code_btn.grid(row=5, column=1, padx=8, pady=8, sticky="e")
        rem_btn.grid(row=5, column=2, padx=16, pady=8, sticky="e")

    def totp_add(self):
        if pyotp is None or keyring is None:
            self.t_codes.delete("1.0","end"); self.t_codes.insert("end","Install: pip install pyotp keyring")
            return
        label = self.t_label.get().strip()
        secret = self.t_secret.get().strip().replace(" ", "")
        if not label or not secret:
            return
        try:
            _ = pyotp.TOTP(secret).now()
        except:
            self.t_codes.delete("1.0","end"); self.t_codes.insert("end","Invalid TOTP secret.")
            return
        svc = f"{APP}:{label}"
        keyring.set_password(APP, svc, secret)
        idx = load_index(); idx[label] = {"created": datetime.utcnow().isoformat()+"Z"}; save_index(idx)
        self.t_codes.delete("1.0","end"); self.t_codes.insert("end",f"Stored secret for '{label}'.")

    def totp_code(self):
        if pyotp is None or keyring is None:
            self.t_codes.delete("1.0","end"); self.t_codes.insert("end","Install: pip install pyotp keyring")
            return
        label = self.t_code_label.get().strip()
        if not label: return
        svc = f"{APP}:{label}"
        secret = keyring.get_password(APP, svc)
        if not secret:
            self.t_codes.delete("1.0","end"); self.t_codes.insert("end","No secret stored for that label.")
            return
        code = pyotp.TOTP(secret).now()
        self.clipboard_clear(); self.clipboard_append(code)
        self.t_codes.delete("1.0","end"); self.t_codes.insert("end",f"{label}: {code} (copied)")

    def totp_list(self):
        idx = load_index()
        self.t_codes.delete("1.0","end")
        if not idx:
            self.t_codes.insert("end","No TOTP labels stored.")
            return
        for k, v in idx.items():
            self.t_codes.insert("end",f"{k}  added={v.get('created','')}\n")

    def totp_remove(self):
        if keyring is None:
            self.t_codes.delete("1.0","end"); self.t_codes.insert("end","Install: pip install keyring")
            return
        label = self.t_code_label.get().strip()
        if not label: return
        svc = f"{APP}:{label}"
        try:
            keyring.delete_password(APP, svc)
        except:
            pass
        idx = load_index()
        if label in idx:
            del idx[label]; save_index(idx)
        self.t_codes.delete("1.0","end"); self.t_codes.insert("end",f"Removed '{label}'")

    def build_letters(self):
        frame = self.tab_letters
        frame.grid_columnconfigure(0, weight=1)
        form = ctk.CTkFrame(frame, corner_radius=12)
        form.grid(row=0, column=0, padx=16, pady=16, sticky="we")
        for i in range(6): form.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(form, text="Name").grid(row=0, column=0, padx=8, pady=6, sticky="e")
        self.lt_name = ctk.CTkEntry(form); self.lt_name.grid(row=0, column=1, padx=6, pady=6, sticky="we")
        ctk.CTkLabel(form, text="Email").grid(row=0, column=2, padx=8, pady=6, sticky="e")
        self.lt_email = ctk.CTkEntry(form); self.lt_email.grid(row=0, column=3, padx=6, pady=6, sticky="we")
        ctk.CTkLabel(form, text="Signature").grid(row=0, column=4, padx=8, pady=6, sticky="e")
        self.lt_sign = ctk.CTkEntry(form); self.lt_sign.grid(row=0, column=5, padx=6, pady=6, sticky="we")

        ctk.CTkLabel(form, text="Infringing URLs (comma-separated)").grid(row=1, column=0, padx=8, pady=6, sticky="e")
        self.lt_infr = ctk.CTkEntry(form); self.lt_infr.grid(row=1, column=1, columnspan=5, padx=6, pady=6, sticky="we")

        ctk.CTkLabel(form, text="Original URLs/Description").grid(row=2, column=0, padx=8, pady=6, sticky="e")
        self.lt_orig = ctk.CTkEntry(form); self.lt_orig.grid(row=2, column=1, columnspan=5, padx=6, pady=6, sticky="we")

        make_dmca = ctk.CTkButton(form, text="Generate DMCA .txt", command=self.make_dmca, corner_radius=12)
        make_dmca.grid(row=3, column=0, padx=8, pady=8, sticky="w")

        ctk.CTkLabel(form, text="Identifiers for deletion request (comma-separated)").grid(row=4, column=0, padx=8, pady=6, sticky="e")
        self.lt_ids = ctk.CTkEntry(form); self.lt_ids.grid(row=4, column=1, columnspan=3, padx=6, pady=6, sticky="we")

        self.law_var = ctk.StringVar(value="GDPR")
        law_box = ctk.CTkComboBox(form, values=["GDPR","CCPA/CPRA","Other"], variable=self.law_var)
        law_box.grid(row=4, column=4, padx=6, pady=6, sticky="we")

        make_priv = ctk.CTkButton(form, text="Generate Privacy Deletion .txt", command=self.make_privacy, corner_radius=12)
        make_priv.grid(row=4, column=5, padx=8, pady=8, sticky="e")

        self.lt_out = ctk.CTkTextbox(frame, height=340, corner_radius=12)
        self.lt_out.grid(row=1, column=0, padx=16, pady=(0,16), sticky="nsew")
        frame.grid_rowconfigure(1, weight=1)

    def write_txt(self, prefix, content):
        fn = f"{prefix}_{int(time.time())}.txt"
        with open(fn, "w", encoding="utf-8") as f:
            f.write(content)
        self.lt_out.delete("1.0","end")
        self.lt_out.insert("end", f"Wrote {fn}\n\n{content}")

    def make_dmca(self):
        name = self.lt_name.get().strip()
        email = self.lt_email.get().strip()
        sign = self.lt_sign.get().strip() or name
        infr = [u.strip() for u in self.lt_infr.get().split(",") if u.strip()]
        orig = self.lt_orig.get().strip() or "Description of the original work owned by me."
        if not (name and email and sign and infr):
            self.lt_out.delete("1.0","end"); self.lt_out.insert("end","Missing fields for DMCA.")
            return
        letter = dmca_letter(name, email, infr, orig, sign)
        self.write_txt("dmca", letter)

    def make_privacy(self):
        name = self.lt_name.get().strip()
        email = self.lt_email.get().strip()
        ids = [i.strip() for i in self.lt_ids.get().split(",") if i.strip()]
        law = self.law_var.get()
        if not (name and email and ids):
            self.lt_out.delete("1.0","end"); self.lt_out.insert("end","Missing fields for privacy deletion request.")
            return
        letter = privacy_erasure_letter(name, email, ids, law)
        self.write_txt("erasure_request", letter)

    def build_portals(self):
        frame = self.tab_portals
        frame.grid_columnconfigure(0, weight=1)
        cols = ctk.CTkFrame(frame, corner_radius=12)
        cols.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        for i in range(3): cols.grid_columnconfigure(i, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        a = ctk.CTkFrame(cols, corner_radius=12); a.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        b = ctk.CTkFrame(cols, corner_radius=12); b.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        c = ctk.CTkFrame(cols, corner_radius=12); c.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")
        for box, title in [(a,"Account Deletion"),(b,"Data Brokers"),(c,"Search/Removal")]:
            ctk.CTkLabel(box, text=title, font=("Inter", 14, "bold")).pack(anchor="w", padx=10, pady=(10,6))

        acct_list = ACCOUNT_PAGES
        for key, url in acct_list.items():
            ctk.CTkButton(a, text=key, corner_radius=12, command=lambda u=url: webbrowser.open(u)).pack(fill="x", padx=10, pady=4)
        for key, url in DATA_BROKERS.items():
            ctk.CTkButton(b, text=key, corner_radius=12, command=lambda u=url: webbrowser.open(u)).pack(fill="x", padx=10, pady=4)
        for key, url in REMOVAL_PORTALS.items():
            ctk.CTkButton(c, text=key, corner_radius=12, command=lambda u=url: webbrowser.open(u)).pack(fill="x", padx=10, pady=4)

if __name__ == "__main__":
    App().mainloop()