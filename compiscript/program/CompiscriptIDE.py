"""
Compiscript IDE - Simple Integrated Development Environment
Allows users to write, edit, and compile Compiscript code
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import tempfile
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from SemanticAnalyzer import SemanticAnalyzer

class CompiscriptIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Compiscript IDE")
        self.root.geometry("1200x800")
        
        # Current file
        self.current_file = None
        self.file_modified = False
        
        self.setup_ui()
        self.setup_menu()
        self.load_sample_code()
    
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Compile menu
        compile_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Compile", menu=compile_menu)
        compile_menu.add_command(label="Compile", command=self.compile_code, accelerator="F5")
        compile_menu.add_command(label="Clear Output", command=self.clear_output)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<F5>', lambda e: self.compile_code())
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="New", command=self.new_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Compile (F5)", command=self.compile_code).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(toolbar, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT)
        
        # Paned window for editor and output
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Editor frame
        editor_frame = ttk.LabelFrame(paned_window, text="Code Editor", padding=5)
        paned_window.add(editor_frame, weight=3)
        
        # Code editor with line numbers
        editor_container = ttk.Frame(editor_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers
        self.line_numbers = tk.Text(editor_container, width=4, padx=3, takefocus=0,
                                   border=0, state='disabled', wrap='none')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Code editor
        self.code_editor = scrolledtext.ScrolledText(editor_container, wrap=tk.NONE,
                                                    font=('Consolas', 11))
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind events for line numbers and modification tracking
        self.code_editor.bind('<KeyRelease>', self.on_text_change)
        self.code_editor.bind('<Button-1>', self.on_text_change)
        self.code_editor.bind('<MouseWheel>', self.on_text_change)
        
        # Output frame
        output_frame = ttk.LabelFrame(paned_window, text="Compilation Output", padding=5)
        paned_window.add(output_frame, weight=1)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, height=10, 
                                                    font=('Consolas', 10),
                                                    state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.output_text.tag_configure("error", foreground="red")
        self.output_text.tag_configure("success", foreground="green")
        self.output_text.tag_configure("info", foreground="blue")
    
    def update_line_numbers(self):
        """Update line numbers in the editor"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        # Get number of lines in editor
        lines = self.code_editor.get(1.0, tk.END).count('\\n')
        line_numbers_string = "\\n".join(str(i) for i in range(1, lines + 1))
        
        self.line_numbers.insert(1.0, line_numbers_string)
        self.line_numbers.config(state='disabled')
    
    def on_text_change(self, event=None):
        """Handle text changes in the editor"""
        self.update_line_numbers()
        if not self.file_modified:
            self.file_modified = True
            self.update_title()
    
    def update_title(self):
        """Update window title"""
        title = "Compiscript IDE"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        if self.file_modified:
            title += " *"
        self.root.title(title)
    
    def new_file(self):
        """Create a new file"""
        if self.file_modified:
            if not self.ask_save_changes():
                return
        
        self.code_editor.delete(1.0, tk.END)
        self.current_file = None
        self.file_modified = False
        self.update_title()
        self.status_var.set("New file created")
    
    def open_file(self):
        """Open an existing file"""
        if self.file_modified:
            if not self.ask_save_changes():
                return
        
        file_path = filedialog.askopenfilename(
            title="Open Compiscript File",
            filetypes=[("Compiscript files", "*.cps"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.insert(1.0, content)
                self.current_file = file_path
                self.file_modified = False
                self.update_title()
                self.status_var.set(f"Opened: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\\n{str(e)}")
    
    def save_file(self):
        """Save the current file"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
    
    def save_as_file(self):
        """Save file with a new name"""
        file_path = filedialog.asksaveasfilename(
            title="Save Compiscript File",
            defaultextension=".cps",
            filetypes=[("Compiscript files", "*.cps"), ("All files", "*.*")]
        )
        
        if file_path:
            self.save_to_file(file_path)
            self.current_file = file_path
            self.update_title()
    
    def save_to_file(self, file_path):
        """Save content to specified file"""
        try:
            content = self.code_editor.get(1.0, tk.END + '-1c')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            self.file_modified = False
            self.update_title()
            self.status_var.set(f"Saved: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\\n{str(e)}")
    
    def ask_save_changes(self):
        """Ask user if they want to save changes"""
        result = messagebox.askyesnocancel(
            "Save Changes",
            "Do you want to save changes to the current file?"
        )
        
        if result is True:  # Yes
            self.save_file()
            return not self.file_modified  # Return True if save was successful
        elif result is False:  # No
            return True
        else:  # Cancel
            return False
    
    def compile_code(self):
        """Compile the current code"""
        self.clear_output()
        self.append_output("Starting compilation...\\n", "info")
        
        # Get code from editor
        code = self.code_editor.get(1.0, tk.END + '-1c')
        
        if not code.strip():
            self.append_output("Error: No code to compile\\n", "error")
            return
        
        # Save to temporary file
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cps', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            # Compile the temporary file
            success, errors = self.run_semantic_analysis(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Display results
            if success:
                self.append_output("Compilation successful! No semantic errors found.\\n", "success")
                self.status_var.set("Compilation successful")
            else:
                self.append_output(f"Compilation failed with {len(errors)} error(s):\\n", "error")
                for i, error in enumerate(errors, 1):
                    self.append_output(f"{i}. {error}\\n", "error")
                self.status_var.set(f"Compilation failed ({len(errors)} errors)")
        
        except Exception as e:
            self.append_output(f"Compilation error: {str(e)}\\n", "error")
            self.status_var.set("Compilation error")
    
    def run_semantic_analysis(self, file_path):
        """Run semantic analysis on a file"""
        try:
            input_stream = FileStream(file_path)
            lexer = CompiscriptLexer(input_stream)
            stream = CommonTokenStream(lexer)
            parser = CompiscriptParser(stream)
            
            # Parse the program
            tree = parser.program()
            
            # Check for syntax errors
            if parser.getNumberOfSyntaxErrors() > 0:
                return False, [f"Syntax errors found: {parser.getNumberOfSyntaxErrors()}"]
            
            # Semantic Analysis
            semantic_analyzer = SemanticAnalyzer()
            walker = ParseTreeWalker()
            walker.walk(semantic_analyzer, tree)
            
            # Return results
            has_errors = semantic_analyzer.has_errors()
            errors = semantic_analyzer.get_errors()
            
            return not has_errors, errors
            
        except Exception as e:
            return False, [f"Exception during compilation: {str(e)}"]
    
    def clear_output(self):
        """Clear the output area"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def append_output(self, text, tag=None):
        """Append text to output area"""
        self.output_text.config(state=tk.NORMAL)
        if tag:
            self.output_text.insert(tk.END, text, tag)
        else:
            self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Compiscript IDE v1.0

A simple IDE for the Compiscript programming language.

Features:
• Syntax highlighting
• Semantic analysis
• Error reporting
• File management

Developed for Compilers Course
Universidad del Valle de Guatemala"""
        
        messagebox.showinfo("About Compiscript IDE", about_text)
    
    def load_sample_code(self):
        """Load sample code into the editor"""
        sample_code = '''// Welcome to Compiscript IDE!
// This is a sample program demonstrating language features

// Constants and variables
const PI: integer = 314;
let radius: integer = 5;
let area: integer;

// Function definition
function calculateArea(r: integer): integer {
    return PI * r * r / 100;  // Simplified calculation
}

// Calculate area
area = calculateArea(radius);

// Control flow
if (area > 50) {
    print("Large circle");
} else {
    print("Small circle");
}

// Loop example
for (let i: integer = 1; i <= 3; i = i + 1) {
    print("Iteration: " + i);
}

// Class example
class Shape {
    let name: string;
    
    function constructor(name: string) {
        this.name = name;
    }
    
    function getName(): string {
        return this.name;
    }
}

let circle: Shape = new Shape("Circle");
print("Shape: " + circle.getName());

print("Program completed successfully!");'''
        
        self.code_editor.insert(1.0, sample_code)
        self.update_line_numbers()

def main():
    """Main function to run the IDE"""
    root = tk.Tk()
    app = CompiscriptIDE(root)
    root.mainloop()

if __name__ == "__main__":
    main()
