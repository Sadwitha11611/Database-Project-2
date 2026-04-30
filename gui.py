"""
gui.py — Milestone 2 GUI for CS-4347 Airport Management System
Run:
  python gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import date


# ── Colour palette ────────────────────────────────────────────────────────────
BG        = "#0d1117"
SURFACE   = "#161b22"
SURFACE2  = "#21262d"
BORDER    = "#30363d"
ACCENT    = "#2f81f7"
ACCENT2   = "#f78166"
GREEN     = "#3fb950"
YELLOW    = "#d29922"
TEXT      = "#e6edf3"
MUTED     = "#8b949e"
WHITE     = "#ffffff"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_TITLE  = ("Courier New", 22, "bold")
FONT_HEAD   = ("Courier New", 12, "bold")
FONT_BODY   = ("Courier New", 11)
FONT_SMALL  = ("Courier New", 10)
FONT_LABEL  = ("Courier New", 10, "bold")
FONT_MONO   = ("Courier New", 11)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(v):
    if v is None:
        return "—"
    s = str(v)
    # timedelta from MySQL TIME columns → "H:MM:SS" → trim to "H:MM"
    if ":" in s and len(s) == 8 and s[2] == ":":
        return s[:5]
    return s


def styled_button(parent, text, command, color=ACCENT, width=18):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=WHITE,
        font=FONT_LABEL,
        relief="flat", bd=0,
        padx=14, pady=8,
        cursor="hand2",
        activebackground=WHITE, activeforeground=color,
        width=width,
    )
    return btn


def input_field(parent, label_text, width=24):
    """Returns (frame, entry_widget)."""
    frame = tk.Frame(parent, bg=SURFACE)
    lbl = tk.Label(frame, text=label_text, bg=SURFACE, fg=MUTED,
                   font=FONT_SMALL, anchor="w")
    lbl.pack(anchor="w", padx=4, pady=(6, 1))
    entry = tk.Entry(frame, bg=SURFACE2, fg=TEXT, insertbackground=TEXT,
                     font=FONT_MONO, relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, width=width)
    entry.pack(fill="x", padx=4, pady=(0, 4), ipady=6)
    return frame, entry


def section_label(parent, text):
    f = tk.Frame(parent, bg=BG)
    tk.Label(f, text=text, bg=BG, fg=ACCENT,
             font=("Courier New", 10, "bold"),
             anchor="w").pack(side="left", padx=(0, 8))
    tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x", expand=True)
    f.pack(fill="x", pady=(14, 6))


# ─────────────────────────────────────────────────────────────────────────────
#  RESULT TABLE
# ─────────────────────────────────────────────────────────────────────────────

class ResultTable(tk.Frame):
    """Scrollable table that accepts a list-of-dicts."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._build()

    def _build(self):
        # Scrollbars
        self.yscroll = tk.Scrollbar(self, orient="vertical", bg=SURFACE2,
                                    troughcolor=SURFACE, width=12)
        self.xscroll = tk.Scrollbar(self, orient="horizontal", bg=SURFACE2,
                                    troughcolor=SURFACE, width=12)
        self.tree = ttk.Treeview(
            self,
            yscrollcommand=self.yscroll.set,
            xscrollcommand=self.xscroll.set,
            selectmode="browse",
        )
        self.yscroll.config(command=self.tree.yview)
        self.xscroll.config(command=self.tree.xview)

        self.yscroll.pack(side="right", fill="y")
        self.xscroll.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=SURFACE, foreground=TEXT,
                        fieldbackground=SURFACE, rowheight=28,
                        font=FONT_BODY, borderwidth=0)
        style.configure("Treeview.Heading",
                        background=SURFACE2, foreground=MUTED,
                        font=FONT_LABEL, relief="flat", borderwidth=0)
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", WHITE)])

    def load(self, rows, columns=None):
        self.tree.delete(*self.tree.get_children())

        if not rows:
            self.tree["columns"] = ("msg",)
            self.tree.column("msg", anchor="w", width=400)
            self.tree.heading("msg", text="Result")
            self.tree.insert("", "end", values=("No results found.",))
            return

        if columns is None:
            columns = list(rows[0].keys())

        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        for col in columns:
            display = col.replace("_", " ").title()
            self.tree.column(col, anchor="w", width=max(120, len(display) * 10))
            self.tree.heading(col, text=display, anchor="w")

        for i, row in enumerate(rows):
            vals = [_fmt(row.get(c)) for c in columns]
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=vals, tags=(tag,))

        self.tree.tag_configure("even", background=SURFACE)
        self.tree.tag_configure("odd",  background=SURFACE2)


# ─────────────────────────────────────────────────────────────────────────────
#  STATUS BAR
# ─────────────────────────────────────────────────────────────────────────────

class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE2, height=28)
        self._var = tk.StringVar(value="Ready")
        self._lbl = tk.Label(self, textvariable=self._var,
                             bg=SURFACE2, fg=MUTED, font=FONT_SMALL,
                             anchor="w", padx=12)
        self._lbl.pack(side="left", fill="both")

    def set(self, msg, color=MUTED):
        self._var.set(msg)
        self._lbl.config(fg=color)

    def ok(self, msg):   self.set(f"✔  {msg}", GREEN)
    def err(self, msg):  self.set(f"✘  {msg}", ACCENT2)
    def busy(self, msg): self.set(f"⟳  {msg}", YELLOW)


# ─────────────────────────────────────────────────────────────────────────────
#  BASE TAB
# ─────────────────────────────────────────────────────────────────────────────

class BaseTab(tk.Frame):
    def __init__(self, parent, status_bar: StatusBar):
        super().__init__(parent, bg=BG)
        self.status = status_bar

    def _run_async(self, fn, on_done):
        """Run fn() in a thread; call on_done(result) on the main thread."""
        def worker():
            try:
                result = fn()
                self.after(0, lambda: on_done(result, None))
            except Exception as exc:
                self.after(0, lambda: on_done(None, exc))
        threading.Thread(target=worker, daemon=True).start()

    def _error_popup(self, exc):
        msg = str(exc)
        if "mysql" in msg.lower() or "connect" in msg.lower():
            msg = ("Cannot connect to MySQL.\n\n"
                   "Make sure:\n"
                   "  • MySQL is running\n"
                   "  • config.ini credentials are correct\n"
                   "  • airport_db database exists\n\n"
                   f"Detail: {exc}")
        messagebox.showerror("Database Error", msg)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 — FLIGHT SEARCH
# ─────────────────────────────────────────────────────────────────────────────

class FlightTab(BaseTab):
    def __init__(self, parent, status_bar):
        super().__init__(parent, status_bar)
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="✈  Flight Lookup", bg=BG, fg=TEXT,
                 font=FONT_TITLE).pack(side="left")

        tk.Label(self,
                 text="Retrieve full details for a flight number — legs, schedule & fares.",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=26, pady=(0, 16))

        # Input row
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=(0, 12))

        fn_frame, self.fn_entry = input_field(row, "FLIGHT NUMBER", width=18)
        fn_frame.pack(side="left", padx=(0, 12))
        self.fn_entry.insert(0, "1000")
        self.fn_entry.bind("<Return>", lambda e: self._search())

        btn = styled_button(row, "Search Flight", self._search, width=16)
        btn.pack(side="left", padx=(0, 12), pady=(20, 0))

        # Results sections
        section_label(self, "FLIGHT INFO")
        self.tbl_flight = ResultTable(self, height=3)
        self.tbl_flight.pack(fill="x", padx=24, pady=(0, 4))

        section_label(self, "LEGS")
        self.tbl_legs = ResultTable(self, height=5)
        self.tbl_legs.pack(fill="x", padx=24, pady=(0, 4))

        section_label(self, "FARES")
        self.tbl_fares = ResultTable(self, height=4)
        self.tbl_fares.pack(fill="x", padx=24, pady=(0, 16))

    def _search(self):
        fn = self.fn_entry.get().strip()
        if not fn:
            messagebox.showwarning("Input needed", "Please enter a flight number.")
            return
        self.status.busy(f"Looking up flight {fn}…")

        def query():
            from queries import flight
            return flight(fn)

        def done(result, err):
            if err:
                self.status.err("Query failed")
                self._error_popup(err)
                return
            flight_row, legs, fares = result
            if not flight_row:
                self.status.err(f"No flight found: {fn}")
                self.tbl_flight.load([])
                self.tbl_legs.load([])
                self.tbl_fares.load([])
                return
            self.tbl_flight.load([flight_row])
            self.tbl_legs.load(legs or [])
            self.tbl_fares.load(fares or [])
            self.status.ok(f"Flight {fn} — {len(legs or [])} leg(s), {len(fares or [])} fare(s)")

        self._run_async(query, done)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 — TRIP SEARCH
# ─────────────────────────────────────────────────────────────────────────────

class TripTab(BaseTab):
    def __init__(self, parent, status_bar):
        super().__init__(parent, status_bar)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="🗺  Trip Planner", bg=BG, fg=TEXT,
                 font=FONT_TITLE).pack(side="left")

        tk.Label(self,
                 text="Find direct & one-stop itineraries. Use airport codes (DFW) or city names (Dallas).",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=26, pady=(0, 16))

        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=(0, 12))

        src_frame, self.src_entry = input_field(row, "ORIGIN", width=18)
        src_frame.pack(side="left", padx=(0, 12))
        self.src_entry.insert(0, "DFW")

        dst_frame, self.dst_entry = input_field(row, "DESTINATION", width=18)
        dst_frame.pack(side="left", padx=(0, 12))
        self.dst_entry.insert(0, "SFO")
        self.dst_entry.bind("<Return>", lambda e: self._search())

        btn = styled_button(row, "Search Trip", self._search, width=14)
        btn.pack(side="left", padx=(0, 12), pady=(20, 0))

        section_label(self, "DIRECT FLIGHTS")
        self.tbl_direct = ResultTable(self, height=6)
        self.tbl_direct.pack(fill="x", padx=24, pady=(0, 4))

        section_label(self, "ONE-STOP CONNECTING FLIGHTS")
        self.tbl_connect = ResultTable(self, height=7)
        self.tbl_connect.pack(fill="x", padx=24, pady=(0, 16))

    def _search(self):
        src = self.src_entry.get().strip()
        dst = self.dst_entry.get().strip()
        if not src or not dst:
            messagebox.showwarning("Input needed", "Please enter both origin and destination.")
            return
        self.status.busy(f"Searching {src} → {dst}…")

        def query():
            from queries import trip
            return trip(src, dst)

        def done(result, err):
            if err:
                self.status.err("Query failed")
                self._error_popup(err)
                return
            direct, connecting, error = result
            if error:
                self.status.err(error)
                messagebox.showwarning("Not found", error)
                return
            self.tbl_direct.load(direct or [])
            self.tbl_connect.load(connecting or [])
            nd, nc = len(direct or []), len(connecting or [])
            self.status.ok(f"{nd} direct, {nc} connecting flight(s) found")

        self._run_async(query, done)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 3 — AIRCRAFT UTILIZATION
# ─────────────────────────────────────────────────────────────────────────────

class UtilizationTab(BaseTab):
    def __init__(self, parent, status_bar):
        super().__init__(parent, status_bar)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="📊  Aircraft Utilization", bg=BG, fg=TEXT,
                 font=FONT_TITLE).pack(side="left")

        tk.Label(self,
                 text="Total flights per aircraft for a date range. Helps schedule maintenance.",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=26, pady=(0, 16))

        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=(0, 12))

        s_frame, self.start_entry = input_field(row, "START DATE (YYYY-MM-DD)", width=16)
        s_frame.pack(side="left", padx=(0, 12))
        self.start_entry.insert(0, "2025-01-01")

        e_frame, self.end_entry = input_field(row, "END DATE (YYYY-MM-DD)", width=16)
        e_frame.pack(side="left", padx=(0, 12))
        self.end_entry.insert(0, str(date.today()))
        self.end_entry.bind("<Return>", lambda e: self._run())

        btn = styled_button(row, "Run Report", self._run, color=GREEN, width=14)
        btn.pack(side="left", padx=(0, 12), pady=(20, 0))

        section_label(self, "UTILIZATION REPORT")
        self.tbl = ResultTable(self)
        self.tbl.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _run(self):
        start = self.start_entry.get().strip()
        end   = self.end_entry.get().strip()
        if not start or not end:
            messagebox.showwarning("Input needed", "Please enter both dates.")
            return
        self.status.busy("Generating utilization report…")

        def query():
            from queries import aircraft_utilization
            return aircraft_utilization(start, end)

        def done(result, err):
            if err:
                self.status.err("Query failed")
                self._error_popup(err)
                return
            self.tbl.load(result or [])
            self.status.ok(f"{len(result or [])} aircraft in report")

        self._run_async(query, done)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 4 — SEAT AVAILABILITY
# ─────────────────────────────────────────────────────────────────────────────

class SeatTab(BaseTab):
    def __init__(self, parent, status_bar):
        super().__init__(parent, status_bar)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="💺  Seat Availability", bg=BG, fg=TEXT,
                 font=FONT_TITLE).pack(side="left")

        tk.Label(self,
                 text="Compare airplane capacity vs. confirmed reservations for a flight + date.",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=26, pady=(0, 16))

        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=(0, 12))

        fn_frame, self.fn_entry = input_field(row, "FLIGHT NUMBER", width=14)
        fn_frame.pack(side="left", padx=(0, 12))
        self.fn_entry.insert(0, "1000")

        dt_frame, self.date_entry = input_field(row, "DATE (YYYY-MM-DD)", width=16)
        dt_frame.pack(side="left", padx=(0, 12))
        self.date_entry.insert(0, "2025-10-04")
        self.date_entry.bind("<Return>", lambda e: self._check())

        btn = styled_button(row, "Check Seats", self._check, width=14)
        btn.pack(side="left", padx=(0, 12), pady=(20, 0))

        # Summary cards row
        self.cards_frame = tk.Frame(self, bg=BG)
        self.cards_frame.pack(fill="x", padx=24, pady=(8, 8))

        section_label(self, "SEAT AVAILABILITY DETAIL")
        self.tbl = ResultTable(self)
        self.tbl.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _stat_card(self, parent, label, value, color):
        f = tk.Frame(parent, bg=SURFACE, padx=20, pady=14)
        f.pack(side="left", padx=(0, 12), pady=4)
        tk.Label(f, text=label, bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w")
        tk.Label(f, text=str(value), bg=SURFACE, fg=color,
                 font=("Courier New", 26, "bold")).pack(anchor="w")

    def _check(self):
        fn   = self.fn_entry.get().strip()
        date_val = self.date_entry.get().strip()
        if not fn or not date_val:
            messagebox.showwarning("Input needed", "Please enter a flight number and date.")
            return
        self.status.busy(f"Checking seats for {fn} on {date_val}…")

        def query():
            from queries import seat_availability
            rows = seat_availability(fn, date_val)
            for row in rows:
                booked    = row.get("booked_seats") or 0
                max_seats = row.get("Max_seats") or 0
                row["computed_remaining_seats"] = max_seats - booked
            return rows

        def done(result, err):
            if err:
                self.status.err("Query failed")
                self._error_popup(err)
                return

            # Clear old cards
            for w in self.cards_frame.winfo_children():
                w.destroy()

            if result:
                # Aggregate across legs
                total_max    = sum(r.get("Max_seats") or 0 for r in result)
                total_booked = sum(r.get("booked_seats") or 0 for r in result)
                total_remain = sum(r.get("computed_remaining_seats") or 0 for r in result)
                remain_color = GREEN if total_remain > total_max * 0.2 else ACCENT2

                self._stat_card(self.cards_frame, "TOTAL SEATS", total_max, ACCENT)
                self._stat_card(self.cards_frame, "BOOKED",      total_booked, YELLOW)
                self._stat_card(self.cards_frame, "REMAINING",   total_remain, remain_color)

            self.tbl.load(result or [])
            self.status.ok(f"{len(result or [])} leg instance(s) found")

        self._run_async(query, done)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 5 — PASSENGER ITINERARY
# ─────────────────────────────────────────────────────────────────────────────

class ItineraryTab(BaseTab):
    def __init__(self, parent, status_bar):
        super().__init__(parent, status_bar)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(hdr, text="🧾  Passenger Itinerary", bg=BG, fg=TEXT,
                 font=FONT_TITLE).pack(side="left")

        tk.Label(self,
                 text="Look up all booked flight legs for a passenger by name or phone number.",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=26, pady=(0, 16))

        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=(0, 12))

        p_frame, self.pass_entry = input_field(row, "PASSENGER NAME OR PHONE", width=28)
        p_frame.pack(side="left", padx=(0, 12))
        self.pass_entry.insert(0, "John Smith")
        self.pass_entry.bind("<Return>", lambda e: self._search())

        btn = styled_button(row, "Find Itinerary", self._search, width=16)
        btn.pack(side="left", padx=(0, 12), pady=(20, 0))

        section_label(self, "BOOKING DETAILS")
        self.tbl = ResultTable(self)
        self.tbl.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _search(self):
        passenger = self.pass_entry.get().strip()
        if not passenger:
            messagebox.showwarning("Input needed", "Please enter a passenger name or phone.")
            return
        self.status.busy(f"Retrieving itinerary for '{passenger}'…")

        def query():
            from queries import passenger_itinerary
            return passenger_itinerary(passenger)

        def done(result, err):
            if err:
                self.status.err("Query failed")
                self._error_popup(err)
                return
            self.tbl.load(result or [])
            n = len(result or [])
            self.status.ok(f"{n} booking(s) found for '{passenger}'") if n else \
                self.status.err(f"No bookings found for '{passenger}'")

        self._run_async(query, done)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION WINDOW
# ─────────────────────────────────────────────────────────────────────────────

class AirportApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AeroBase  |  CS-4347 Airport Management System")
        self.geometry("1100x760")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._build()

    def _build(self):
        # ── Top banner ────────────────────────────────────────────────────────
        banner = tk.Frame(self, bg=SURFACE2, height=52)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        tk.Label(banner,
                 text="✈  AEROBASE",
                 bg=SURFACE2, fg=ACCENT,
                 font=("Courier New", 16, "bold"),
                 padx=20).pack(side="left", pady=12)

        tk.Label(banner,
                 text="CS-4347 · Airport Management System · Milestone 3",
                 bg=SURFACE2, fg=MUTED,
                 font=FONT_SMALL).pack(side="left", pady=12)

        # DB status indicator
        self.db_dot = tk.Label(banner, text="●", bg=SURFACE2, fg=YELLOW,
                               font=("Courier New", 14))
        self.db_dot.pack(side="right", padx=(0, 8), pady=12)
        tk.Label(banner, text="MySQL", bg=SURFACE2, fg=MUTED,
                 font=FONT_SMALL).pack(side="right", padx=(0, 4), pady=12)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status = StatusBar(self)
        self.status.pack(side="bottom", fill="x")

        # ── Tab strip ─────────────────────────────────────────────────────────
        tab_strip = tk.Frame(self, bg=SURFACE2, height=44)
        tab_strip.pack(fill="x")

        self.notebook = ttk.Notebook(self)

        # style notebook tabs
        style = ttk.Style()
        style.configure("TNotebook", background=SURFACE2, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=SURFACE2, foreground=MUTED,
                        font=FONT_LABEL,
                        padding=[18, 10])
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", TEXT)])

        self.notebook.pack(fill="both", expand=True)

        tabs = [
            ("✈  Flight",        FlightTab),
            ("🗺  Trip",          TripTab),
            ("📊  Utilization",   UtilizationTab),
            ("💺  Seats",         SeatTab),
            ("🧾  Itinerary",     ItineraryTab),
        ]

        for name, cls in tabs:
            frame = cls(self.notebook, self.status)
            self.notebook.add(frame, text=name)

        # ── Test DB connection on startup ─────────────────────────────────────
        self.after(400, self._ping_db)

    def _ping_db(self):
        def check():
            from db import get_connection, close_connection
            conn = get_connection()
            close_connection(conn)
            return True

        def done(result, err):
            if err:
                self.db_dot.config(fg=ACCENT2)
                self.status.err("Cannot connect to MySQL — check config.ini")
            else:
                self.db_dot.config(fg=GREEN)
                self.status.ok("Connected to MySQL airport_db")

        def worker():
            try:
                r = check()
                self.after(0, lambda: done(r, None))
            except Exception as e:
                self.after(0, lambda: done(None, e))

        threading.Thread(target=worker, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = AirportApp()
    app.mainloop()
