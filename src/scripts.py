import os
import subprocess
import glob
from pathlib import Path

def compile_latex():
    """Compile all LaTeX files from output/ directory to build/ directory."""
    
    # Create build directory if it doesn't exist
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)
    
    # Find all .tex files in output directory
    tex_files = glob.glob("output/*.tex")
    
    if not tex_files:
        print("No .tex files found in output/ directory")
        return
    
    print(f"Found {len(tex_files)} .tex file(s) to compile:")
    
    for tex_file in tex_files:
        print(f"  Compiling {tex_file}...")
        try:
            # Run pdflatex with output directory set to build
            result = subprocess.run([
                "pdflatex", 
                "-output-directory=build", 
                tex_file
            ], 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                print(f"    ✓ Successfully compiled {tex_file}")
            else:
                print(f"    ✗ Failed to compile {tex_file}")
                print(f"    Error: {result.stderr}")
                
        except FileNotFoundError:
            print(f"    ✗ pdflatex not found. Please make sure MiKTeX is installed and in PATH.")
            break
        except Exception as e:
            print(f"    ✗ Error compiling {tex_file}: {e}")
    
    print("Compilation complete!")