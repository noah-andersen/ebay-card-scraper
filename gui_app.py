#!/usr/bin/env python3
"""
eBay Card Scraper GUI Application
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
import sys

# Import utility functions
from utils.convert_to_csv import json_to_csv, json_to_csv_with_stats
from utils.filter import filter_csv

# Set appearance and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ScraperGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("eBay Card Scraper - Modern GUI")
        self.geometry("1100x800")
        
        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()
        
        # Initialize variables
        self.scraper_process = None
        self.is_scraping = False
        
    def create_sidebar(self):
        """Create sidebar with navigation"""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="🎴 Card Scraper",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Navigation buttons
        self.scraper_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Scraper",
            command=lambda: self.show_frame("scraper")
        )
        self.scraper_btn.grid(row=1, column=0, padx=20, pady=10)
        
        self.filter_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Filter Data",
            command=lambda: self.show_frame("filter")
        )
        self.filter_btn.grid(row=2, column=0, padx=20, pady=10)
        
        self.converter_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Convert to CSV",
            command=lambda: self.show_frame("converter")
        )
        self.converter_btn.grid(row=3, column=0, padx=20, pady=10)
        
        self.settings_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Settings",
            command=lambda: self.show_frame("settings")
        )
        self.settings_btn.grid(row=4, column=0, padx=20, pady=10)
        
        # Appearance mode
        self.appearance_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Appearance:",
            anchor="w"
        )
        self.appearance_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        
        self.appearance_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dark", "Light", "System"],
            command=self.change_appearance
        )
        self.appearance_menu.grid(row=8, column=0, padx=20, pady=(10, 20))
        
    def create_main_content(self):
        """Create main content area with tabs"""
        # Create container for all frames
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create all frames
        self.frames = {}
        self.frames["scraper"] = self.create_scraper_frame()
        self.frames["filter"] = self.create_filter_frame()
        self.frames["converter"] = self.create_converter_frame()
        self.frames["settings"] = self.create_settings_frame()
        
        # Show scraper frame by default
        self.show_frame("scraper")
        
    def create_scraper_frame(self):
        """Create scraper configuration frame"""
        frame = ctk.CTkFrame(self.main_frame)
        frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            frame,
            text="Web Scraper Configuration",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        # Description
        desc = ctk.CTkLabel(
            frame,
            text="Configure and run the web scraper to collect graded Pokemon card data",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        desc.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")
        
        # Create scrollable frame for inputs
        scroll_frame = ctk.CTkScrollableFrame(frame, label_text="Scraper Options")
        scroll_frame.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        frame.grid_rowconfigure(2, weight=1)
        
        # Source selection
        ctk.CTkLabel(scroll_frame, text="Source:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        self.source_var = ctk.StringVar(value="ebay")
        source_frame = ctk.CTkFrame(scroll_frame)
        source_frame.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")
        
        ctk.CTkRadioButton(
            source_frame, text="eBay", variable=self.source_var, value="ebay"
        ).pack(side="left", padx=10, pady=5)
        ctk.CTkRadioButton(
            source_frame, text="Mercari", variable=self.source_var, value="mercari"
        ).pack(side="left", padx=10, pady=5)
        
        # Search query
        ctk.CTkLabel(scroll_frame, text="Search Query:", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        self.search_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="e.g., PSA 10 Pokemon Card, Charizard CGC 9.5",
            width=400
        )
        self.search_entry.grid(row=3, column=0, padx=10, pady=(0, 15), sticky="ew")
        self.search_entry.insert(0, "PSA 10 Pokemon Card")
        
        # Max pages
        ctk.CTkLabel(scroll_frame, text="Maximum Pages:", font=ctk.CTkFont(weight="bold")).grid(
            row=4, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        self.max_pages_var = ctk.StringVar(value="5")
        self.max_pages_entry = ctk.CTkEntry(
            scroll_frame,
            textvariable=self.max_pages_var,
            width=100
        )
        self.max_pages_entry.grid(row=5, column=0, padx=10, pady=(0, 15), sticky="w")
        
        # Grading companies filter
        ctk.CTkLabel(scroll_frame, text="Filter by Grading Company:", font=ctk.CTkFont(weight="bold")).grid(
            row=6, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        grading_frame = ctk.CTkFrame(scroll_frame)
        grading_frame.grid(row=7, column=0, padx=10, pady=(0, 15), sticky="ew")
        
        self.grading_vars = {}
        companies = ["PSA", "BGS", "CGC", "SGC", "TAG"]
        for i, company in enumerate(companies):
            var = ctk.BooleanVar(value=True)
            self.grading_vars[company] = var
            ctk.CTkCheckBox(grading_frame, text=company, variable=var).grid(
                row=0, column=i, padx=10, pady=5
            )
        
        # Output options
        ctk.CTkLabel(scroll_frame, text="Output Options:", font=ctk.CTkFont(weight="bold")).grid(
            row=8, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        
        self.download_images_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Download Images",
            variable=self.download_images_var
        ).grid(row=9, column=0, padx=10, pady=5, sticky="w")
        
        self.auto_convert_csv_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Auto-convert to CSV",
            variable=self.auto_convert_csv_var
        ).grid(row=10, column=0, padx=10, pady=5, sticky="w")
        
        self.auto_filter_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Auto-filter scraped data",
            variable=self.auto_filter_var
        ).grid(row=11, column=0, padx=10, pady=5, sticky="w")
        
        self.generate_stats_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Generate Statistics",
            variable=self.generate_stats_var
        ).grid(row=12, column=0, padx=10, pady=5, sticky="w")
        
        # Output file
        ctk.CTkLabel(scroll_frame, text="Output Filename:", font=ctk.CTkFont(weight="bold")).grid(
            row=13, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        output_frame = ctk.CTkFrame(scroll_frame)
        output_frame.grid(row=14, column=0, padx=10, pady=(0, 15), sticky="ew")
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.output_entry = ctk.CTkEntry(output_frame, width=300)
        self.output_entry.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        self.output_entry.insert(0, f"scraped_data/output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        ctk.CTkButton(
            output_frame,
            text="Browse",
            width=80,
            command=self.browse_output_file
        ).grid(row=0, column=1, pady=5)
        
        # Console output
        console_label = ctk.CTkLabel(
            frame,
            text="Console Output",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        console_label.grid(row=3, column=0, padx=30, pady=(10, 5), sticky="w")
        
        self.console_text = ctk.CTkTextbox(frame, height=200, width=500)
        self.console_text.grid(row=4, column=0, padx=30, pady=(0, 10), sticky="nsew")
        frame.grid_rowconfigure(4, weight=1)
        
        # Control buttons
        button_frame = ctk.CTkFrame(frame)
        button_frame.grid(row=5, column=0, padx=30, pady=(10, 30), sticky="ew")
        
        self.start_btn = ctk.CTkButton(
            button_frame,
            text="▶ Start Scraping",
            command=self.start_scraping,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="⏹ Stop",
            command=self.stop_scraping,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        return frame
    
    def create_filter_frame(self):
        """Create data filter frame"""
        frame = ctk.CTkFrame(self.main_frame)
        frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            frame,
            text="Data Filter",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            frame,
            text="Filter scraped data based on quality criteria and extract missing grades",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        desc.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")
        
        # Scrollable options
        scroll_frame = ctk.CTkScrollableFrame(frame, label_text="Filter Options")
        scroll_frame.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        frame.grid_rowconfigure(2, weight=1)
        
        # Input file selection
        ctk.CTkLabel(scroll_frame, text="Input CSV File:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        input_frame = ctk.CTkFrame(scroll_frame)
        input_frame.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.filter_input_entry = ctk.CTkEntry(input_frame, width=400)
        self.filter_input_entry.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        
        ctk.CTkButton(
            input_frame,
            text="Browse",
            width=80,
            command=self.browse_filter_input
        ).grid(row=0, column=1, pady=5)
        
        # Filter criteria
        ctk.CTkLabel(scroll_frame, text="Filter Criteria:", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        
        self.filter_low_images_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Remove entries with ≤1 image",
            variable=self.filter_low_images_var
        ).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.filter_thicc_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Remove entries containing 'thicc'",
            variable=self.filter_thicc_var
        ).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        self.filter_multiple_cards_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Remove multiple card listings",
            variable=self.filter_multiple_cards_var
        ).grid(row=5, column=0, padx=10, pady=5, sticky="w")
        
        # NLP options
        ctk.CTkLabel(scroll_frame, text="Grade Extraction:", font=ctk.CTkFont(weight="bold")).grid(
            row=6, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        
        self.use_nlp_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Use NLP to extract missing grades",
            variable=self.use_nlp_var
        ).grid(row=7, column=0, padx=10, pady=5, sticky="w")
        
        self.remove_missing_grades_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Remove entries with no grade after extraction",
            variable=self.remove_missing_grades_var
        ).grid(row=8, column=0, padx=10, pady=5, sticky="w")
        
        # Image management
        ctk.CTkLabel(scroll_frame, text="Image Management:", font=ctk.CTkFont(weight="bold")).grid(
            row=9, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        
        self.delete_images_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            scroll_frame,
            text="Delete images for filtered entries",
            variable=self.delete_images_var
        ).grid(row=10, column=0, padx=10, pady=5, sticky="w")
        
        # Output file
        ctk.CTkLabel(scroll_frame, text="Output File:", font=ctk.CTkFont(weight="bold")).grid(
            row=11, column=0, padx=10, pady=(15, 5), sticky="w"
        )
        output_frame = ctk.CTkFrame(scroll_frame)
        output_frame.grid(row=12, column=0, padx=10, pady=(0, 15), sticky="ew")
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.filter_output_entry = ctk.CTkEntry(output_frame, width=400)
        self.filter_output_entry.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        self.filter_output_entry.insert(0, "Auto (adds _filtered suffix)")
        
        ctk.CTkButton(
            output_frame,
            text="Browse",
            width=80,
            command=self.browse_filter_output
        ).grid(row=0, column=1, pady=5)
        
        # Console
        console_label = ctk.CTkLabel(
            frame,
            text="Filter Output",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        console_label.grid(row=3, column=0, padx=30, pady=(10, 5), sticky="w")
        
        self.filter_console = ctk.CTkTextbox(frame, height=200, width=500)
        self.filter_console.grid(row=4, column=0, padx=30, pady=(0, 10), sticky="nsew")
        frame.grid_rowconfigure(4, weight=1)
        
        # Buttons
        button_frame = ctk.CTkFrame(frame)
        button_frame.grid(row=5, column=0, padx=30, pady=(10, 30), sticky="ew")
        
        ctk.CTkButton(
            button_frame,
            text="🔍 Run Filter",
            command=self.run_filter,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        return frame
    
    def create_converter_frame(self):
        """Create JSON to CSV converter frame"""
        frame = ctk.CTkFrame(self.main_frame)
        frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            frame,
            text="JSON to CSV Converter",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            frame,
            text="Convert scraped JSON data to CSV format with statistics",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        desc.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")
        
        # Options
        options_frame = ctk.CTkFrame(frame)
        options_frame.grid(row=2, column=0, padx=30, pady=10, sticky="ew")
        options_frame.grid_columnconfigure(0, weight=1)
        
        # Input file
        ctk.CTkLabel(options_frame, text="Input JSON File:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        input_frame = ctk.CTkFrame(options_frame)
        input_frame.grid(row=1, column=0, padx=10, pady=(0, 15), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.converter_input_entry = ctk.CTkEntry(input_frame, width=400)
        self.converter_input_entry.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        
        ctk.CTkButton(
            input_frame,
            text="Browse",
            width=80,
            command=self.browse_converter_input
        ).grid(row=0, column=1, pady=5)
        
        # Options
        self.converter_stats_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text="Generate statistics file",
            variable=self.converter_stats_var
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        # Console
        console_label = ctk.CTkLabel(
            frame,
            text="Conversion Output",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        console_label.grid(row=3, column=0, padx=30, pady=(10, 5), sticky="w")
        
        self.converter_console = ctk.CTkTextbox(frame, height=400, width=500)
        self.converter_console.grid(row=4, column=0, padx=30, pady=(0, 10), sticky="nsew")
        frame.grid_rowconfigure(4, weight=1)
        
        # Button
        button_frame = ctk.CTkFrame(frame)
        button_frame.grid(row=5, column=0, padx=30, pady=(10, 30), sticky="ew")
        
        ctk.CTkButton(
            button_frame,
            text="📊 Convert to CSV",
            command=self.run_converter,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40
        ).pack(padx=5, expand=True, fill="x")
        
        return frame
    
    def create_settings_frame(self):
        """Create settings frame"""
        frame = ctk.CTkFrame(self.main_frame)
        frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            frame,
            text="Settings",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")
        
        desc = ctk.CTkLabel(
            frame,
            text="Configure advanced scraper settings",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        desc.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")
        
        # Scrollable settings
        scroll_frame = ctk.CTkScrollableFrame(frame, label_text="Advanced Settings")
        scroll_frame.grid(row=2, column=0, padx=30, pady=10, sticky="nsew")
        frame.grid_rowconfigure(2, weight=1)
        
        # Concurrency settings
        ctk.CTkLabel(scroll_frame, text="Concurrency:", font=ctk.CTkFont(weight="bold", size=16)).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        
        ctk.CTkLabel(scroll_frame, text="Concurrent Requests:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.concurrent_requests_var = ctk.StringVar(value="8")
        ctk.CTkEntry(scroll_frame, textvariable=self.concurrent_requests_var, width=100).grid(
            row=1, column=1, padx=10, pady=5, sticky="w"
        )
        
        ctk.CTkLabel(scroll_frame, text="Download Delay (seconds):").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.download_delay_var = ctk.StringVar(value="2")
        ctk.CTkEntry(scroll_frame, textvariable=self.download_delay_var, width=100).grid(
            row=2, column=1, padx=10, pady=5, sticky="w"
        )
        
        # Image settings
        ctk.CTkLabel(scroll_frame, text="Image Quality:", font=ctk.CTkFont(weight="bold", size=16)).grid(
            row=3, column=0, padx=10, pady=(20, 5), sticky="w"
        )
        
        ctk.CTkLabel(scroll_frame, text="Minimum Width (px):").grid(
            row=4, column=0, padx=10, pady=5, sticky="w"
        )
        self.min_width_var = ctk.StringVar(value="400")
        ctk.CTkEntry(scroll_frame, textvariable=self.min_width_var, width=100).grid(
            row=4, column=1, padx=10, pady=5, sticky="w"
        )
        
        ctk.CTkLabel(scroll_frame, text="Minimum Height (px):").grid(
            row=5, column=0, padx=10, pady=5, sticky="w"
        )
        self.min_height_var = ctk.StringVar(value="400")
        ctk.CTkEntry(scroll_frame, textvariable=self.min_height_var, width=100).grid(
            row=5, column=1, padx=10, pady=5, sticky="w"
        )
        
        # Browser settings
        ctk.CTkLabel(scroll_frame, text="Browser:", font=ctk.CTkFont(weight="bold", size=16)).grid(
            row=6, column=0, padx=10, pady=(20, 5), sticky="w"
        )
        
        self.headless_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(scroll_frame, text="Headless Mode", variable=self.headless_var).grid(
            row=7, column=0, columnspan=2, padx=10, pady=5, sticky="w"
        )
        
        # Save button
        button_frame = ctk.CTkFrame(frame)
        button_frame.grid(row=3, column=0, padx=30, pady=(10, 30), sticky="ew")
        
        ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40
        ).pack(padx=5, expand=True, fill="x")
        
        return frame
    
    def show_frame(self, frame_name):
        """Show specified frame"""
        for name, frame in self.frames.items():
            if name == frame_name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_remove()
    
    def change_appearance(self, mode):
        """Change appearance mode"""
        ctk.set_appearance_mode(mode.lower())
    
    def browse_output_file(self):
        """Browse for output file location"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)
    
    def browse_filter_input(self):
        """Browse for filter input file"""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.filter_input_entry.delete(0, tk.END)
            self.filter_input_entry.insert(0, filename)
    
    def browse_filter_output(self):
        """Browse for filter output file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.filter_output_entry.delete(0, tk.END)
            self.filter_output_entry.insert(0, filename)
    
    def browse_converter_input(self):
        """Browse for converter input file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.converter_input_entry.delete(0, tk.END)
            self.converter_input_entry.insert(0, filename)
    
    def log_to_console(self, message, console_widget=None):
        """Log message to console"""
        if console_widget is None:
            console_widget = self.console_text
        console_widget.insert(tk.END, message + "\n")
        console_widget.see(tk.END)
        self.update_idletasks()
    
    def start_scraping(self):
        """Start the scraping process"""
        if self.is_scraping:
            messagebox.showwarning("Already Running", "Scraper is already running!")
            return
        
        # Validate inputs
        search_query = self.search_entry.get().strip()
        if not search_query:
            messagebox.showerror("Error", "Please enter a search query!")
            return
        
        try:
            max_pages = int(self.max_pages_var.get())
            if max_pages <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Max pages must be a positive number!")
            return
        
        # Clear console
        self.console_text.delete("1.0", tk.END)
        
        # Update UI
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.is_scraping = True
        
        # Start scraping in a separate thread
        thread = threading.Thread(target=self._run_scraper, daemon=True)
        thread.start()
    
    def _run_scraper(self):
        """Run the scraper (called in separate thread)"""
        try:
            source = self.source_var.get()
            search_query = self.search_entry.get().strip()
            max_pages = self.max_pages_var.get()
            output_file = self.output_entry.get().strip()
            
            # Build scrapy command
            spider_name = f"{source}_graded_cards"
            cmd = [
                "scrapy", "crawl", spider_name,
                "-a", f"search_query={search_query}",
                "-a", f"max_pages={max_pages}",
                "-O", output_file
            ]
            
            self.log_to_console(f"Starting scraper: {' '.join(cmd)}")
            self.log_to_console("=" * 60)
            
            # Run scrapy process
            self.scraper_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Stream output
            for line in self.scraper_process.stdout:
                self.log_to_console(line.rstrip())
            
            self.scraper_process.wait()
            
            if self.scraper_process.returncode == 0:
                self.log_to_console("=" * 60)
                self.log_to_console("✅ Scraping completed successfully!")
                
                # Auto-convert if enabled
                csv_file = None
                if self.auto_convert_csv_var.get():
                    self.log_to_console("\nAuto-converting to CSV...")
                    csv_file = self._convert_to_csv(output_file)
                
                # Auto-filter if enabled and CSV was created
                if self.auto_filter_var.get() and csv_file:
                    self.log_to_console("\nAuto-filtering data...")
                    self._auto_filter_csv(csv_file)
            else:
                self.log_to_console("=" * 60)
                self.log_to_console("❌ Scraping failed!")
        
        except Exception as e:
            self.log_to_console(f"Error: {str(e)}")
        
        finally:
            # Reset UI
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.is_scraping = False
            self.scraper_process = None
    
    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraper_process:
            self.log_to_console("\n⏹ Stopping scraper...")
            self.scraper_process.terminate()
            self.scraper_process = None
        self.is_scraping = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
    
    def _convert_to_csv(self, json_file):
        """Convert JSON to CSV"""
        try:
            self.log_to_console(f"\n📊 Converting {json_file} to CSV...")
            
            if self.generate_stats_var.get():
                # Convert with statistics
                result = json_to_csv_with_stats(json_file)
                self.log_to_console(f"✅ CSV created: {result['csv']}")
                self.log_to_console(f"✅ Statistics saved: {result['stats']}")
                return result['csv']
            else:
                # Convert without statistics
                csv_path = json_to_csv(json_file)
                self.log_to_console(f"✅ CSV created: {csv_path}")
                return csv_path
                
        except Exception as e:
            self.log_to_console(f"❌ Conversion failed: {str(e)}")
            return None
    
    def _auto_filter_csv(self, csv_file):
        """Auto-filter CSV data"""
        try:
            import io
            import sys
            
            self.log_to_console(f"\n🔍 Auto-filtering {csv_file}...")
            
            # Use default filter settings
            output_file = None  # Will add _filtered suffix automatically
            delete_images = True
            use_nlp = True
            
            # Redirect stdout to capture print statements
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                # Call filter function
                filter_csv(
                    input_file=csv_file,
                    output_file=output_file,
                    delete_images=delete_images,
                    use_nlp=use_nlp
                )
            finally:
                # Restore stdout
                sys.stdout = old_stdout
                
                # Get captured output and display key info
                output = captured_output.getvalue()
                # Only show summary lines to avoid cluttering console
                for line in output.split('\n'):
                    if line.strip() and any(keyword in line for keyword in ['SUMMARY', 'Total', 'kept', 'filtered', 'extracted', 'deleted', 'saved to']):
                        self.log_to_console(line)
            
            self.log_to_console("✅ Auto-filtering completed!")
            
        except Exception as e:
            sys.stdout = old_stdout  # Ensure stdout is restored
            self.log_to_console(f"❌ Auto-filter failed: {str(e)}")
    
    def run_filter(self):
        """Run the data filter"""
        input_file = self.filter_input_entry.get().strip()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid input CSV file!")
            return
        
        # Clear console
        self.filter_console.delete("1.0", tk.END)
        
        # Run filter in thread
        thread = threading.Thread(target=self._run_filter_thread, args=(input_file,), daemon=True)
        thread.start()
    
    def _run_filter_thread(self, input_file):
        """Run filter in separate thread"""
        try:
            import io
            import sys
            
            output_file = self.filter_output_entry.get().strip()
            if output_file == "Auto (adds _filtered suffix)":
                output_file = None
            
            delete_images = self.delete_images_var.get()
            use_nlp = self.use_nlp_var.get()
            
            self.log_to_console(f"Running filter on: {input_file}", self.filter_console)
            self.log_to_console("=" * 60, self.filter_console)
            
            # Redirect stdout to capture print statements
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                # Call filter function directly
                filter_csv(
                    input_file=input_file,
                    output_file=output_file,
                    delete_images=delete_images,
                    use_nlp=use_nlp
                )
            finally:
                # Restore stdout
                sys.stdout = old_stdout
                
                # Get captured output and display it
                output = captured_output.getvalue()
                for line in output.split('\n'):
                    if line.strip():
                        self.log_to_console(line, self.filter_console)
            
            self.log_to_console("✅ Filtering completed!", self.filter_console)
        
        except Exception as e:
            sys.stdout = old_stdout  # Ensure stdout is restored
            self.log_to_console(f"❌ Error: {str(e)}", self.filter_console)
    
    def run_converter(self):
        """Run JSON to CSV converter"""
        input_file = self.converter_input_entry.get().strip()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid input JSON file!")
            return
        
        # Clear console
        self.converter_console.delete("1.0", tk.END)
        
        # Run converter in thread
        thread = threading.Thread(target=self._run_converter_thread, args=(input_file,), daemon=True)
        thread.start()
    
    def _run_converter_thread(self, input_file):
        """Run converter in separate thread"""
        try:
            self.log_to_console(f"Converting: {input_file}", self.converter_console)
            self.log_to_console("=" * 60, self.converter_console)
            
            # Call conversion function directly
            if self.converter_stats_var.get():
                result = json_to_csv_with_stats(input_file)
                self.log_to_console(f"✅ CSV created: {result['csv']}", self.converter_console)
                self.log_to_console(f"✅ Statistics saved: {result['stats']}", self.converter_console)
            else:
                csv_path = json_to_csv(input_file)
                self.log_to_console(f"✅ CSV created: {csv_path}", self.converter_console)
            
            self.log_to_console("✅ Conversion completed!", self.converter_console)
        
        except Exception as e:
            self.log_to_console(f"❌ Error: {str(e)}", self.converter_console)
    
    def save_settings(self):
        """Save settings to configuration file"""
        settings = {
            "concurrent_requests": self.concurrent_requests_var.get(),
            "download_delay": self.download_delay_var.get(),
            "min_width": self.min_width_var.get(),
            "min_height": self.min_height_var.get(),
            "headless": self.headless_var.get()
        }
        
        try:
            with open("gui_settings.json", "w") as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def load_settings(self):
        """Load settings from configuration file"""
        try:
            if os.path.exists("gui_settings.json"):
                with open("gui_settings.json", "r") as f:
                    settings = json.load(f)
                    self.concurrent_requests_var.set(settings.get("concurrent_requests", "8"))
                    self.download_delay_var.set(settings.get("download_delay", "2"))
                    self.min_width_var.set(settings.get("min_width", "400"))
                    self.min_height_var.set(settings.get("min_height", "400"))
                    self.headless_var.set(settings.get("headless", True))
        except Exception as e:
            print(f"Failed to load settings: {str(e)}")


def main():
    """Main entry point"""
    app = ScraperGUI()
    app.load_settings()
    app.mainloop()


if __name__ == "__main__":
    main()
