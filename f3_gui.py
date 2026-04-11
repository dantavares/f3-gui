#!/usr/bin/env python3
"""
F3 - Fight Flash Fraud
Interface gráfica para as ferramentas f3write, f3read e f3probe
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import shutil
import re
from datetime import datetime


# ─── Paleta de cores ──────────────────────────────────────────────────────────
BG        = "#0e1117"
BG2       = "#161b25"
BG3       = "#1e2535"
BORDER    = "#2a3347"
ACCENT    = "#00d4aa"
ACCENT2   = "#0099ff"
WARN      = "#ff6b35"
SUCCESS   = "#00c853"
ERROR     = "#ff3d3d"
TEXT      = "#e8eaf0"
TEXT_DIM  = "#7a8499"
MONO      = "Courier New"


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ─── Widgets personalizados ───────────────────────────────────────────────────

class FlatButton(tk.Button):
    def __init__(self, parent, text, command=None, color=ACCENT,
                 text_color=BG, width=160, height=38, font_size=11, **kwargs):
        # Calcula largura em caracteres aproximada (tkinter usa chars, não px)
        char_w = max(1, width // (font_size * 8 // 10 + 2))
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=text_color,
            activebackground=self._darken(color),
            activeforeground=text_color,
            relief="flat",
            bd=0,
            font=(MONO, font_size, "bold"),
            cursor="hand2",
            padx=8,
            pady=6,
            **kwargs
        )
        self._color    = color
        self._enabled  = True
        self.bind("<Enter>", lambda _: self._hover(True))
        self.bind("<Leave>", lambda _: self._hover(False))

    @staticmethod
    def _darken(hex_color):
        r, g, b = hex_to_rgb(hex_color)
        return "#{:02x}{:02x}{:02x}".format(
            int(r * 0.75), int(g * 0.75), int(b * 0.75))

    def _hover(self, on):
        if not self._enabled:
            return
        self.config(bg=self._darken(self._color) if on else self._color)

    def set_enabled(self, val):
        self._enabled = val
        self.config(
            state="normal" if val else "disabled",
            cursor="hand2" if val else "arrow",
            bg=self._color
        )

    def config_text(self, text):
        self.config(text=text)


class LabeledEntry(tk.Frame):
    def __init__(self, parent, label, placeholder="", width=40, **kwargs):
        super().__init__(parent, bg=BG2, **kwargs)
        tk.Label(self, text=label, bg=BG2, fg=TEXT_DIM,
                 font=("Courier New", 9)).pack(anchor="w", padx=2, pady=(0,2))
        self.var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var, width=width,
                              bg=BG3, fg=TEXT, insertbackground=ACCENT,
                              relief="flat", font=(MONO, 10),
                              highlightthickness=1,
                              highlightbackground=BORDER,
                              highlightcolor=ACCENT)
        self.entry.pack(fill="x", ipady=5, padx=1)
        if placeholder:
            self._ph = placeholder
            self.var.set(placeholder)
            self.entry.config(fg=TEXT_DIM)
            self.entry.bind("<FocusIn>",  self._clear_ph)
            self.entry.bind("<FocusOut>", self._restore_ph)

    def _clear_ph(self, _):
        if self.var.get() == self._ph:
            self.var.set(""); self.entry.config(fg=TEXT)

    def _restore_ph(self, _):
        if not self.var.get():
            self.var.set(self._ph); self.entry.config(fg=TEXT_DIM)

    def get(self):
        v = self.var.get()
        return "" if v == getattr(self, "_ph", None) else v

    def set(self, v):
        self.var.set(v); self.entry.config(fg=TEXT)


class Terminal(tk.Frame):
    """Área de saída estilo terminal."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.text = tk.Text(self, bg="#080c12", fg=TEXT, font=(MONO, 9),
                            state="disabled", relief="flat",
                            insertbackground=ACCENT, wrap="none",
                            highlightthickness=1, highlightbackground=BORDER,
                            padx=8, pady=6)
        sb_y = tk.Scrollbar(self, orient="vertical",
                             command=self.text.yview, bg=BG3)
        sb_x = tk.Scrollbar(self, orient="horizontal",
                             command=self.text.xview, bg=BG3)
        self.text.configure(yscrollcommand=sb_y.set,
                            xscrollcommand=sb_x.set)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.text.pack(fill="both", expand=True)

        # Tags de cor
        self.text.tag_config("accent",  foreground=ACCENT)
        self.text.tag_config("success", foreground=SUCCESS)
        self.text.tag_config("warn",    foreground=WARN)
        self.text.tag_config("error",   foreground=ERROR)
        self.text.tag_config("dim",     foreground=TEXT_DIM)
        self.text.tag_config("blue",    foreground=ACCENT2)

    def write(self, msg, tag=""):
        self.text.config(state="normal")
        if tag:
            self.text.insert("end", msg, tag)
        else:
            self.text.insert("end", msg)
        self.text.see("end")
        self.text.config(state="disabled")

    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

    def header(self, title):
        sep = "─" * 60
        self.write(f"\n{sep}\n", "dim")
        self.write(f"  {title}\n", "accent")
        self.write(f"{sep}\n", "dim")

    def timestamp(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.write(f"  [{now}]\n", "dim")


class ProgressRow(tk.Frame):
    def __init__(self, parent, label, **kwargs):
        super().__init__(parent, bg=BG2, **kwargs)
        tk.Label(self, text=label, bg=BG2, fg=TEXT_DIM,
                 font=(MONO, 9), width=18, anchor="w").pack(side="left")
        self.bar = ttk.Progressbar(self, mode="determinate", length=320)
        self.bar.pack(side="left", padx=(6,8))
        self.pct = tk.Label(self, text="  0%", bg=BG2, fg=ACCENT,
                            font=(MONO, 9, "bold"), width=6)
        self.pct.pack(side="left")

    def set(self, value):
        v = max(0, min(100, value))
        self.bar["value"] = v
        self.pct.config(text=f"{v:4.1f}%")

    def reset(self):
        self.set(0)


# ─── Janela principal ─────────────────────────────────────────────────────────

class F3App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("F3 — Fight Flash Fraud")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._process = None
        self._running = False

        self._check_f3()
        self._build_ui()
        # Deixa o tkinter calcular o tamanho ideal e centraliza
        self.update_idletasks()
        w = max(900, self.winfo_reqwidth())
        h = max(780, self.winfo_reqheight())
        self._center(w, h)
        self.minsize(w, h)
        # Detecta dispositivos logo após a janela aparecer
        self.after(200, self._refresh_devices)

    def _center(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _check_f3(self):
        self._has_write = shutil.which("f3write") is not None
        self._has_read  = shutil.which("f3read")  is not None
        self._has_probe = shutil.which("f3probe")  is not None
        self._has_fix   = shutil.which("f3fix")    is not None

    # ── Detecção de dispositivos ──────────────────────────────────────────────

    @staticmethod
    def _list_devices():
        import json
        try:
            out = subprocess.check_output(
                ["lsblk", "-J", "-o",
                 "NAME,SIZE,TYPE,MOUNTPOINT,LABEL,VENDOR,MODEL,RM"],
                stderr=subprocess.DEVNULL, text=True
            )
            data = json.loads(out)
        except Exception:
            return []

        result = []

        def walk(nodes, parent_rm=False):
            for node in nodes or []:
                rm = bool(node.get("rm")) or parent_rm
                typ = node.get("type", "")
                name = node.get("name", "")
                size = node.get("size") or ""
                mount = node.get("mountpoint") or ""
                label = (node.get("label") or "").strip()
                vendor = (node.get("vendor") or "").strip()
                model  = (node.get("model") or "").strip()
                if typ in ("disk", "part") and rm:
                    result.append({
                        "name": name, "path": f"/dev/{name}",
                        "size": size, "type": typ,
                        "mount": mount, "label": label,
                        "vendor": vendor, "model": model,
                    })
                walk(node.get("children"), rm)

        walk(data.get("blockdevices", []))
        return result

    @staticmethod
    def _fmt_device(d):
        tag = d["label"] or d["model"] or d["vendor"] or ""
        mount = f"  →  {d['mount']}" if d["mount"] else ""
        marker = "├" if d["type"] == "part" else "◉"
        return f"{marker} {d['path']}  [{d['size']}]  {tag}{mount}"

    def _refresh_devices(self):
        devs = self._list_devices()
        self._devices_data = devs
        dev_labels = [self._fmt_device(d) for d in devs]
        self._dev_combo["values"] = dev_labels or ["(nenhum dispositivo removível detectado)"]
        mounts = [d["mount"] for d in devs if d["mount"]]
        self._mount_combo["values"] = mounts or ["(sem ponto de montagem detectado)"]
        if dev_labels:
            self._dev_combo.current(0)
            self._on_dev_select()
        self._term.write(
            f"  [{len(devs)} dispositivo(s) removível(is) detectado(s)]\n", "dim")

    def _on_dev_select(self, _event=None):
        idx = self._dev_combo.current()
        if idx < 0 or idx >= len(self._devices_data):
            return
        d = self._devices_data[idx]
        self._dev_var.set(d["path"])
        if d["mount"]:
            self._mount_var.set(d["mount"])
            self._mount_combo.set(d["mount"])

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Cabeçalho
        hdr = tk.Frame(self, bg=BG2, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡ F3", bg=BG2, fg=ACCENT,
                 font=(MONO, 22, "bold")).pack(side="left", padx=20)
        tk.Label(hdr, text="Fight Flash Fraud", bg=BG2, fg=TEXT,
                 font=(MONO, 13)).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="● PRONTO", bg=BG2, fg=SUCCESS,
                                    font=(MONO, 10, "bold"))
        self._status_lbl.pack(side="right", padx=20)

        # Separador
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        # Corpo
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Painel esquerdo — rolável para caber todos os controles
        left_outer = tk.Frame(body, bg=BG2, width=318)
        left_outer.pack(side="left", fill="y", padx=(0, 10))
        left_outer.pack_propagate(False)

        left_canvas = tk.Canvas(left_outer, bg=BG2, highlightthickness=0,
                                width=300)
        left_sb = tk.Scrollbar(left_outer, orient="vertical",
                               command=left_canvas.yview, bg=BG3)
        left_canvas.configure(yscrollcommand=left_sb.set)
        left_sb.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        left = tk.Frame(left_canvas, bg=BG2)
        win_id = left_canvas.create_window((0, 0), window=left, anchor="nw")

        def _on_frame_config(e):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        def _on_canvas_resize(e):
            left_canvas.itemconfig(win_id, width=e.width)

        left.bind("<Configure>", _on_frame_config)
        left_canvas.bind("<Configure>", _on_canvas_resize)

        # Scroll com roda do mouse sobre o painel esquerdo
        def _on_mousewheel(e):
            left_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def _on_mousewheel_linux(e):
            left_canvas.yview_scroll(-1 if e.num == 4 else 1, "units")

        left_canvas.bind_all("<MouseWheel>",     _on_mousewheel)
        left_canvas.bind_all("<Button-4>",       _on_mousewheel_linux)
        left_canvas.bind_all("<Button-5>",       _on_mousewheel_linux)

        self._build_controls(left)

        # Painel direito (terminal + progresso)
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_output(right)

    def _section(self, parent, title):
        f = tk.Frame(parent, bg=BG2)
        f.pack(fill="x", pady=(12,4), padx=12)
        tk.Label(f, text=f"▸ {title}", bg=BG2, fg=ACCENT,
                 font=(MONO, 9, "bold")).pack(anchor="w")
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12)
        return f

    def _build_controls(self, parent):
        self._devices_data = []

        # Estilo ttk para combobox escuro
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.TCombobox",
                        fieldbackground=BG3, background=BG3,
                        foreground=TEXT, selectbackground=BORDER,
                        selectforeground=TEXT,
                        arrowcolor=ACCENT, bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER,
                        insertcolor=ACCENT)
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", BG3)],
                  foreground=[("readonly", TEXT)])

        tk.Label(parent, text="CONFIGURAÇÃO", bg=BG2, fg=TEXT_DIM,
                 font=(MONO, 8)).pack(anchor="w", padx=12, pady=(12,0))

        # ── Seleção de dispositivo ────────────────────────────────────────────
        self._section(parent, "Dispositivo removível")
        df = tk.Frame(parent, bg=BG2)
        df.pack(fill="x", padx=12, pady=4)

        tk.Label(df, text="Selecionar:", bg=BG2, fg=TEXT_DIM,
                 font=(MONO, 9)).pack(anchor="w")
        self._dev_combo = ttk.Combobox(df, state="readonly",
                                       style="Dark.TCombobox",
                                       font=(MONO, 8))
        self._dev_combo.pack(fill="x", ipady=4)
        self._dev_combo.bind("<<ComboboxSelected>>", self._on_dev_select)

        tk.Label(df, text="Caminho do dispositivo:", bg=BG2, fg=TEXT_DIM,
                 font=(MONO, 9)).pack(anchor="w", pady=(6,0))
        self._dev_var = tk.StringVar()
        dev_entry = tk.Entry(df, textvariable=self._dev_var,
                             bg=BG3, fg=TEXT, insertbackground=ACCENT,
                             relief="flat", font=(MONO, 9),
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=ACCENT)
        dev_entry.pack(fill="x", ipady=4)

        FlatButton(df, "↺ Atualizar lista", command=self._refresh_devices,
                   color=BG3, text_color=ACCENT, height=28,
                   font_size=9).pack(anchor="e", pady=(5,0))

        # ── Ponto de montagem ─────────────────────────────────────────────────
        self._section(parent, "Ponto de Montagem (f3write / f3read)")
        mf = tk.Frame(parent, bg=BG2)
        mf.pack(fill="x", padx=12, pady=4)

        tk.Label(mf, text="Partições montadas:", bg=BG2, fg=TEXT_DIM,
                 font=(MONO, 9)).pack(anchor="w")
        self._mount_combo = ttk.Combobox(mf, state="readonly",
                                         style="Dark.TCombobox",
                                         font=(MONO, 8))
        self._mount_combo.pack(fill="x", ipady=4)
        self._mount_combo.bind("<<ComboboxSelected>>",
                               lambda e: self._mount_var.set(
                                   self._mount_combo.get()))

        tk.Label(mf, text="Caminho manual / confirmar:", bg=BG2, fg=TEXT_DIM,
                 font=(MONO, 9)).pack(anchor="w", pady=(6,0))
        self._mount_var = tk.StringVar()
        tk.Entry(mf, textvariable=self._mount_var,
                 bg=BG3, fg=TEXT, insertbackground=ACCENT,
                 relief="flat", font=(MONO, 9),
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=ACCENT).pack(fill="x", ipady=4)

        FlatButton(mf, "📂 Procurar", command=self._browse_mount,
                   color=BG3, text_color=TEXT, height=28,
                   font_size=9).pack(anchor="e", pady=(5,0))

        # ── Opções ───────────────────────────────────────────────────────────
        self._section(parent, "Opções")
        of = tk.Frame(parent, bg=BG2)
        of.pack(fill="x", padx=12, pady=4)

        # Campo --last-sec (preenchido automaticamente pelo f3probe)
        ls_row = tk.Frame(of, bg=BG2)
        ls_row.pack(fill="x", pady=(6, 0))
        tk.Label(ls_row, text="--last-sec =", bg=BG2, fg=TEXT_DIM,
                 font=(MONO, 9)).pack(side="left")
        self._last_sec_var = tk.StringVar(value="")
        ls_entry = tk.Entry(ls_row, textvariable=self._last_sec_var,
                            bg=BG3, fg=ACCENT, insertbackground=ACCENT,
                            relief="flat", font=(MONO, 9, "bold"), width=14,
                            highlightthickness=1,
                            highlightbackground=BORDER,
                            highlightcolor=ACCENT)
        ls_entry.pack(side="left", padx=(4, 0), ipady=3)
        self._last_sec_lbl = tk.Label(of, text="Rode f3probe primeiro ⮭",
                                      bg=BG2, fg=TEXT_DIM, font=(MONO, 8))
        self._last_sec_lbl.pack(anchor="w", pady=(2, 0))

        # Botões de ação
        self._section(parent, "Ações")
        bf = tk.Frame(parent, bg=BG2)
        bf.pack(fill="x", padx=12, pady=6)

        self._btn_write = FlatButton(bf, "▶ f3write", command=self._run_write,
                                     color=ACCENT2, width=130, height=36)
        self._btn_write.pack(fill="x", pady=3)

        self._btn_read = FlatButton(bf, "▶ f3read", command=self._run_read,
                                    color=ACCENT, width=130, height=36)
        self._btn_read.pack(fill="x", pady=3)

        self._btn_probe = FlatButton(bf, "▶ f3probe", command=self._run_probe,
                                     color="#9c6bff", width=130, height=36)
        self._btn_probe.pack(fill="x", pady=3)

        self._btn_fix = FlatButton(bf, "▶ f3fix", command=self._run_fix,
                                   color=WARN, width=130, height=36)
        self._btn_fix.pack(fill="x", pady=3)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)

        self._btn_stop = FlatButton(parent, "■ PARAR", command=self._stop,
                                    color=ERROR, width=130, height=34,
                                    font_size=10)
        self._btn_stop.pack(padx=12, pady=2, fill="x")
        self._btn_stop.set_enabled(False)

        FlatButton(parent, "🗑 Limpar saída", command=self._clear,
                   color=BG3, text_color=TEXT_DIM, width=130, height=30,
                   font_size=9).pack(padx=12, pady=(4,0), fill="x")

        # Aviso de ferramentas ausentes
        missing = []
        for t, has in [("f3write", self._has_write), ("f3read", self._has_read),
                       ("f3probe", self._has_probe), ("f3fix", self._has_fix)]:
            if not has:
                missing.append(t)
        if missing:
            tk.Label(parent, text=f"⚠ Não encontrado:\n{', '.join(missing)}",
                     bg=BG2, fg=WARN, font=(MONO, 8), justify="left",
                     wraplength=270).pack(padx=12, pady=8, anchor="w")

    def _build_output(self, parent):
        # Barras de progresso
        pf = tk.Frame(parent, bg=BG2)
        pf.pack(fill="x", pady=(0,8))
        tk.Label(pf, text="PROGRESSO", bg=BG2, fg=TEXT_DIM,
                 font=(MONO, 8)).pack(anchor="w", padx=8, pady=(6,2))
        self._prog_write = ProgressRow(pf, "Escrita")
        self._prog_write.pack(fill="x", padx=8, pady=2)
        self._prog_read  = ProgressRow(pf, "Leitura / Verify")
        self._prog_read.pack(fill="x", padx=8, pady=(2,8))

        # Estilo ttk para progressbar
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Horizontal.TProgressbar",
                        troughcolor=BG3, background=ACCENT,
                        bordercolor=BG3, lightcolor=ACCENT,
                        darkcolor=ACCENT)

        # Terminal
        tk.Label(parent, text="SAÍDA", bg=BG, fg=TEXT_DIM,
                 font=(MONO, 8)).pack(anchor="w")
        self._term = Terminal(parent)
        self._term.pack(fill="both", expand=True)

        # Banner de veredito (oculto até ter resultado)
        self._verdict_frame = tk.Frame(parent, bg=BG, height=0)
        self._verdict_frame.pack(fill="x", pady=(6, 0))
        self._verdict_frame.pack_propagate(False)

        self._verdict_icon  = tk.Label(self._verdict_frame, font=(MONO, 26),
                                       bg=BG)
        self._verdict_icon.pack(side="left", padx=(10, 6), pady=6)

        vtext = tk.Frame(self._verdict_frame, bg=BG)
        vtext.pack(side="left", fill="both", expand=True, pady=6)

        self._verdict_title = tk.Label(vtext, font=(MONO, 13, "bold"),
                                       bg=BG, anchor="w")
        self._verdict_title.pack(fill="x")

        self._verdict_detail = tk.Label(vtext, font=(MONO, 9),
                                        bg=BG, anchor="w", wraplength=520,
                                        justify="left")
        self._verdict_detail.pack(fill="x", pady=(2, 0))

        # Barra inferior
        bot = tk.Frame(parent, bg=BG2)
        bot.pack(fill="x", pady=(6,0))
        self._info_lbl = tk.Label(bot, text="Selecione uma ação para começar.",
                                  bg=BG2, fg=TEXT_DIM, font=(MONO, 9),
                                  anchor="w")
        self._info_lbl.pack(side="left", padx=8, pady=4)

    # ── Navegação ─────────────────────────────────────────────────────────────

    def _browse_mount(self):
        path = filedialog.askdirectory(title="Selecionar ponto de montagem")
        if path:
            self._mount_var.set(path)

    # ── Controle de estado ────────────────────────────────────────────────────

    def _set_running(self, running):
        self._running = running
        state = not running
        for btn in [self._btn_write, self._btn_read,
                    self._btn_probe, self._btn_fix]:
            btn.set_enabled(state)
        self._btn_stop.set_enabled(running)
        self._status_lbl.config(
            text="● EXECUTANDO" if running else "● PRONTO",
            fg=WARN if running else SUCCESS
        )

    def _stop(self):
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
        self._term.write("\n[Processo interrompido pelo usuário]\n", "warn")
        self._set_running(False)

    def _clear(self):
        self._term.clear()
        self._prog_write.reset()
        self._prog_read.reset()
        self._hide_verdict()

    # ── Veredito ──────────────────────────────────────────────────────────────

    def _hide_verdict(self):
        self._verdict_frame.config(height=0)
        self._verdict_frame.pack_propagate(False)

    def _show_verdict(self, genuine, title, detail, color):
        icon = "✅" if genuine else "⚠️"
        self._verdict_icon.config(text=icon)
        self._verdict_title.config(text=title, fg=color)
        self._verdict_detail.config(text=detail, fg=TEXT if genuine else WARN)
        # Linha colorida no topo do banner
        self._verdict_frame.config(
            bg=color, highlightbackground=color,
            highlightthickness=2, height=80)
        self._verdict_icon.config(bg=BG)
        for w in self._verdict_frame.winfo_children():
            try:
                w.config(bg=BG)
                for ww in w.winfo_children():
                    ww.config(bg=BG)
            except Exception:
                pass
        self._verdict_frame.pack_propagate(False)

    @staticmethod
    def _analyze_output(lines):
        """
        Analisa as linhas coletadas de f3read ou f3probe e retorna
        (genuine: bool | None, ok_str, lost_str, probe_msg).
        Retorna None se não houver dados suficientes.
        """
        ok_str   = None
        lost_str = None
        probe_genuine = None
        probe_msg     = ""

        for line in lines:
            # f3read: "Data OK: 14.90 GB (31,260,672 sectors)"
            m = re.search(r'Data OK:\s*(.+)', line, re.IGNORECASE)
            if m:
                ok_str = m.group(1).strip()

            # f3read: "Data LOST: 1.37 GB (2,874,368 sectors)"
            m = re.search(r'Data LOST:\s*(.+)', line, re.IGNORECASE)
            if m:
                lost_str = m.group(1).strip()

            # f3probe: genuíno
            if re.search(r'seems?\s+to\s+be\s+genuine', line, re.IGNORECASE):
                probe_genuine = True
                probe_msg = line.strip()

            # f3probe: falso / counterfeit / fake
            if re.search(r'(counterfeit|fake|not\s+genuine|is\s+a\s+liar)',
                         line, re.IGNORECASE):
                probe_genuine = False
                probe_msg = line.strip()

        # Decisão pelo f3read
        if lost_str is not None:
            # "0.00 Byte" ou "0 Byte" = genuíno
            genuine = bool(re.match(r'0\.?0*\s*Byte', lost_str, re.IGNORECASE))
            return genuine, ok_str, lost_str, probe_genuine, probe_msg

        # Decisão só pelo f3probe
        if probe_genuine is not None:
            return probe_genuine, ok_str, lost_str, probe_genuine, probe_msg

        return None, ok_str, lost_str, probe_genuine, probe_msg

    def _show_result_verdict(self, lines, cmd_name):
        genuine, ok_str, lost_str, probe_gen, probe_msg = self._analyze_output(lines)

        if genuine is None:
            return  # Sem dados suficientes para veredito

        dev = self._dev_var.get().strip() or "o dispositivo"

        if genuine:
            title  = f"🎉  Parabéns! {dev} é GENUÍNO."
            parts  = []
            if ok_str:
                parts.append(f"Dados OK: {ok_str}")
            if lost_str:
                parts.append(f"Dados perdidos: {lost_str}")
            if probe_msg:
                parts.append(probe_msg)
            detail = "  |  ".join(parts) if parts else \
                     "O dispositivo passou na verificação com sucesso."
            self.after(0, lambda: self._show_verdict(True, title, detail, SUCCESS))
        else:
            title = f"⛔  ATENÇÃO! {dev} tem TAMANHO FALSO."
            parts = []
            if lost_str:
                parts.append(f"Dados corrompidos / inacessíveis: {lost_str}")
            if ok_str:
                parts.append(f"Dados OK (capacidade real): {ok_str}")
            if probe_msg:
                parts.append(probe_msg)
            parts.append(
                "Sugestão: execute o f3probe para detectar a capacidade real, "
                "depois use o f3fix para corrigir a tabela de partições."
            )
            detail = "\n".join(parts)
            self.after(0, lambda: self._show_verdict(False, title, detail, ERROR))

    # ── Execução de comandos ──────────────────────────────────────────────────

    def _run_cmd(self, cmd, title, prog_row=None, parse_fn=None,
                 show_verdict=False):
        if self._running:
            return
        self._set_running(True)
        self._hide_verdict()
        self._prog_write.reset()
        self._prog_read.reset()
        self._term.header(title)
        self._term.timestamp()
        self._term.write(f"  $ {' '.join(cmd)}\n\n", "blue")
        self._info_lbl.config(text=f"Executando: {cmd[0]} …")
        collected = []

        def worker():
            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                for line in self._process.stdout:
                    collected.append(line)
                    self._handle_line(line, prog_row, parse_fn)
                self._process.wait()
                rc = self._process.returncode
                if rc == 0:
                    self.after(0, lambda: self._term.write(
                        "\n✔ Concluído com sucesso.\n", "success"))
                else:
                    self.after(0, lambda: self._term.write(
                        f"\n✘ Processo encerrado (código {rc}).\n", "error"))
                if show_verdict:
                    self._show_result_verdict(collected, cmd[0])
            except FileNotFoundError:
                self.after(0, lambda: self._term.write(
                    f"\n✘ Comando não encontrado: {cmd[0]}\n"
                    "  Instale o f3: https://github.com/AltraMayor/f3\n",
                    "error"))
            except Exception as e:
                self.after(0, lambda: self._term.write(
                    f"\n✘ Erro: {e}\n", "error"))
            finally:
                self.after(0, lambda: self._set_running(False))
                self.after(0, lambda: self._info_lbl.config(text="Pronto."))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_line(self, line, prog_row, parse_fn):
        tag = ""
        l = line.lower()
        if any(w in l for w in ("error", "erro", "failed", "falha")):
            tag = "error"
        elif any(w in l for w in ("ok", "success", "good", "pass")):
            tag = "success"
        elif any(w in l for w in ("warn", "aviso", "caution")):
            tag = "warn"

        self.after(0, lambda ln=line, t=tag: self._term.write(ln, t))

        if parse_fn and prog_row:
            pct = parse_fn(line)
            if pct is not None:
                self.after(0, lambda v=pct: prog_row.set(v))

    # ── Parsers de progresso ──────────────────────────────────────────────────

    @staticmethod
    def _parse_write(line):
        m = re.search(r'\((\d+(?:\.\d+)?)%\)', line)
        if m:
            return float(m.group(1))
        return None

    @staticmethod
    def _parse_read(line):
        m = re.search(r'\((\d+(?:\.\d+)?)%\)', line)
        if m:
            return float(m.group(1))
        return None

    def _parse_probe_line(self, line):
        """Extrai --last-sec=N da saída do f3probe e atualiza o campo."""
        # f3probe sugere o comando:  f3fix --last-sec=29675000 /dev/sdb
        m = re.search(r'--last-sec[= ](\d+)', line)
        if m:
            val = m.group(1)
            self.after(0, lambda v=val: self._set_last_sec(v))
        return self._parse_read(line)

    def _set_last_sec(self, val):
        self._last_sec_var.set(val)
        self._last_sec_lbl.config(
            text="  ✔ capturado do f3probe", fg=SUCCESS)
        self._term.write(
            f"  → --last-sec={val} capturado e pronto para f3fix\n", "success")

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _run_write(self):
        mount = self._mount_var.get().strip()
        if not mount:
            messagebox.showwarning("Atenção", "Informe o ponto de montagem.")
            return
        if not os.path.isdir(mount):
            if not messagebox.askyesno("Caminho não encontrado",
                                       f"'{mount}' não existe. Continuar mesmo assim?"):
                return
        self._run_cmd(["f3write", mount],
                      "f3write — Gravando dados de teste",
                      self._prog_write, self._parse_write)

    def _run_read(self):
        mount = self._mount_var.get().strip()
        if not mount:
            messagebox.showwarning("Atenção", "Informe o ponto de montagem.")
            return
        self._run_cmd(["f3read", mount],
                      "f3read — Verificando integridade",
                      self._prog_read, self._parse_read,
                      show_verdict=True)

    def _run_probe(self):
        device = self._dev_var.get().strip()
        if not device:
            messagebox.showwarning("Atenção", "Selecione ou informe o dispositivo.")
            return
        cmd = ["f3probe", "--destructive", device]
        if not messagebox.askyesno(
            "Confirmar f3probe",
            f"f3probe irá APAGAR DADOS em {device}.\n"
            "Tem certeza que deseja continuar?"
        ):
            return
        # Limpa o last-sec anterior antes de rodar
        self._last_sec_var.set("")
        self._last_sec_lbl.config(text="Rode f3probe primeiro ⮭", fg=TEXT_DIM)
        self._run_cmd(cmd, f"f3probe — Sondando {device}",
                      self._prog_read, self._parse_probe_line,
                      show_verdict=True)

    def _run_fix(self):
        device = self._dev_var.get().strip()
        if not device:
            messagebox.showwarning("Atenção", "Selecione ou informe o dispositivo.")
            return
        last_sec = self._last_sec_var.get().strip()
        if not last_sec:
            messagebox.showwarning(
                "--last-sec ausente",
                "O f3fix exige o parâmetro --last-sec.\n\n"
                "Execute o f3probe primeiro — o valor será\n"
                "capturado automaticamente da saída.")
            return
        if not last_sec.isdigit():
            messagebox.showerror("Valor inválido",
                                 f"--last-sec deve ser um número inteiro.\nValor atual: '{last_sec}'")
            return
        if not messagebox.askyesno(
            "Confirmar f3fix",
            f"f3fix irá MODIFICAR a tabela de partições de {device}.\n"
            f"  --last-sec = {last_sec}\n\n"
            "Esta operação é irreversível. Continuar?"
        ):
            return
        self._run_cmd(
            ["f3fix", f"--last-sec={last_sec}", device],
            f"f3fix — Corrigindo {device}  (--last-sec={last_sec})"
        )


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = F3App()
    app.mainloop()
