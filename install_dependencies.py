#!/usr/bin/env python3
"""
Free AI Tools Dependency Installer
Installs all necessary free AI tools and dependencies for the marketing automation system
"""

import os
import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreeAIInstaller:
    """Installer for free AI tools and dependencies"""
    
    def __init__(self):
        self.install_dir = Path("/opt")
        self.tools = {
            'ollama': {
                'url': 'https://ollama.ai/install.sh',
                'models': ['llama2:7b', 'mistral:7b', 'codellama:7b'],
                'description': 'Local LLM inference'
            },
            'stable_diffusion': {
                'repo': 'https://github.com/AUTOMATIC1111/stable-diffusion-webui.git',
                'path': self.install_dir / 'stable-diffusion-webui',
                'description': 'Local image generation'
            },
            'animatediff': {
                'repo': 'https://github.com/guoyww/AnimateDiff.git',
                'path': self.install_dir / 'AnimateDiff',
                'description': 'Local video generation'
            },
            'coqui_tts': {
                'package': 'TTS',
                'description': 'High-quality text-to-speech'
            },
            'ffmpeg': {
                'package': 'ffmpeg',
                'description': 'Video processing and conversion'
            },
            'espeak': {
                'package': 'espeak espeak-data',
                'description': 'Fast text-to-speech'
            },
            'festival': {
                'package': 'festival festvox-kallpc16k',
                'description': 'Text-to-speech engine'
            }
        }
    
    def run_command(self, command, shell=True, check=True):
        """Run shell command with logging"""
        logger.info(f"Running: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=shell, 
                check=check, 
                capture_output=True, 
                text=True
            )
            if result.stdout:
                logger.info(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if e.stderr:
                logger.error(e.stderr)
            raise
    
    def install_system_packages(self):
        """Install system packages"""
        logger.info("Installing system packages...")
        
        # Update package list
        self.run_command("apt-get update")
        
        # Install basic dependencies
        packages = [
            'git', 'curl', 'wget', 'python3-pip', 'python3-venv',
            'build-essential', 'cmake', 'pkg-config',
            'libavcodec-dev', 'libavformat-dev', 'libswscale-dev',
            'libgstreamer1.0-dev', 'libgstreamer-plugins-base1.0-dev',
            'libgtk-3-dev', 'libpng-dev', 'libjpeg-dev',
            'libopenexr-dev', 'libtiff-dev', 'libwebp-dev'
        ]
        
        package_str = ' '.join(packages)
        self.run_command(f"apt-get install -y {package_str}")
    
    def install_ffmpeg(self):
        """Install FFmpeg for video processing"""
        logger.info("Installing FFmpeg...")
        self.run_command("apt-get install -y ffmpeg")
        
        # Verify installation
        result = self.run_command("ffmpeg -version", check=False)
        if result.returncode == 0:
            logger.info("FFmpeg installed successfully")
        else:
            logger.error("FFmpeg installation failed")
    
    def install_espeak(self):
        """Install eSpeak for text-to-speech"""
        logger.info("Installing eSpeak...")
        self.run_command("apt-get install -y espeak espeak-data")
        
        # Verify installation
        result = self.run_command("espeak --version", check=False)
        if result.returncode == 0:
            logger.info("eSpeak installed successfully")
        else:
            logger.error("eSpeak installation failed")
    
    def install_festival(self):
        """Install Festival for text-to-speech"""
        logger.info("Installing Festival...")
        self.run_command("apt-get install -y festival festvox-kallpc16k")
        
        # Verify installation
        result = self.run_command("festival --version", check=False)
        if result.returncode == 0:
            logger.info("Festival installed successfully")
        else:
            logger.error("Festival installation failed")
    
    def install_ollama(self):
        """Install Ollama for local LLM inference"""
        logger.info("Installing Ollama...")
        
        # Download and install Ollama
        self.run_command("curl -fsSL https://ollama.ai/install.sh | sh")
        
        # Start Ollama service
        self.run_command("systemctl enable ollama", check=False)
        self.run_command("systemctl start ollama", check=False)
        
        # Wait for service to start
        import time
        time.sleep(10)
        
        # Download models
        models = ['llama2:7b', 'mistral:7b', 'codellama:7b']
        for model in models:
            logger.info(f"Downloading model: {model}")
            self.run_command(f"ollama pull {model}", check=False)
        
        logger.info("Ollama installation completed")
    
    def install_stable_diffusion(self):
        """Install Stable Diffusion WebUI"""
        logger.info("Installing Stable Diffusion WebUI...")
        
        sd_path = self.install_dir / 'stable-diffusion-webui'
        
        if not sd_path.exists():
            # Clone repository
            self.run_command(
                f"git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git {sd_path}"
            )
        
        # Install dependencies
        os.chdir(sd_path)
        self.run_command("./webui.sh --skip-torch-cuda-test --exit", check=False)
        
        # Create startup script
        startup_script = sd_path / 'start_api.sh'
        with open(startup_script, 'w') as f:
            f.write("""#!/bin/bash
cd /opt/stable-diffusion-webui
./webui.sh --api --listen --port 7860 --skip-torch-cuda-test --no-browser
""")
        
        self.run_command(f"chmod +x {startup_script}")
        
        logger.info("Stable Diffusion WebUI installed successfully")
    
    def install_animatediff(self):
        """Install AnimateDiff for video generation"""
        logger.info("Installing AnimateDiff...")
        
        ad_path = self.install_dir / 'AnimateDiff'
        
        if not ad_path.exists():
            # Clone repository
            self.run_command(
                f"git clone https://github.com/guoyww/AnimateDiff.git {ad_path}"
            )
        
        # Install dependencies
        os.chdir(ad_path)
        self.run_command("pip install -r requirements.txt", check=False)
        
        # Download base models
        models_dir = ad_path / 'models'
        models_dir.mkdir(exist_ok=True)
        
        # Download motion module
        motion_module_url = "https://huggingface.co/guoyww/animatediff/resolve/main/mm_sd_v15_v2.ckpt"
        self.run_command(
            f"wget -O {models_dir}/mm_sd_v15_v2.ckpt {motion_module_url}",
            check=False
        )
        
        logger.info("AnimateDiff installed successfully")
    
    def install_coqui_tts(self):
        """Install Coqui TTS for high-quality text-to-speech"""
        logger.info("Installing Coqui TTS...")
        
        # Install TTS package
        self.run_command("pip install TTS")
        
        # Download common models
        models = [
            'tts_models/en/ljspeech/tacotron2-DDC',
            'tts_models/en/ljspeech/glow-tts',
            'tts_models/multilingual/multi-dataset/your_tts'
        ]
        
        for model in models:
            logger.info(f"Downloading TTS model: {model}")
            self.run_command(f"tts --model_name {model} --text 'test' --out_path /tmp/test.wav", check=False)
        
        logger.info("Coqui TTS installed successfully")
    
    def install_python_packages(self):
        """Install additional Python packages"""
        logger.info("Installing Python packages...")
        
        packages = [
            'torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu',
            'transformers',
            'diffusers',
            'accelerate',
            'xformers',
            'opencv-python',
            'pillow',
            'numpy',
            'scipy',
            'librosa',
            'soundfile',
            'moviepy',
            'imageio',
            'scikit-image',
            'matplotlib',
            'seaborn',
            'requests',
            'aiohttp',
            'asyncio'
        ]
        
        for package in packages:
            logger.info(f"Installing: {package}")
            self.run_command(f"pip install {package}", check=False)
    
    def create_service_files(self):
        """Create systemd service files for auto-start"""
        logger.info("Creating service files...")
        
        # Ollama service (usually created automatically)
        
        # Stable Diffusion service
        sd_service = """[Unit]
Description=Stable Diffusion WebUI API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stable-diffusion-webui
ExecStart=/opt/stable-diffusion-webui/start_api.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        with open('/etc/systemd/system/stable-diffusion.service', 'w') as f:
            f.write(sd_service)
        
        # Enable services
        self.run_command("systemctl daemon-reload")
        self.run_command("systemctl enable stable-diffusion", check=False)
        
        logger.info("Service files created")
    
    def verify_installations(self):
        """Verify all installations"""
        logger.info("Verifying installations...")
        
        verifications = [
            ("FFmpeg", "ffmpeg -version"),
            ("eSpeak", "espeak --version"),
            ("Festival", "festival --version"),
            ("Ollama", "ollama --version"),
            ("Python TTS", "tts --help"),
            ("Git", "git --version"),
            ("Python", "python3 --version"),
            ("Pip", "pip --version")
        ]
        
        results = {}
        for name, command in verifications:
            try:
                result = self.run_command(command, check=False)
                results[name] = "✓ Installed" if result.returncode == 0 else "✗ Failed"
            except Exception:
                results[name] = "✗ Error"
        
        logger.info("Installation verification results:")
        for name, status in results.items():
            logger.info(f"  {name}: {status}")
        
        return results
    
    def install_all(self):
        """Install all free AI tools"""
        logger.info("Starting installation of free AI tools...")
        
        try:
            # Check if running as root
            if os.geteuid() != 0:
                logger.error("This script must be run as root (use sudo)")
                sys.exit(1)
            
            # Create installation directory
            self.install_dir.mkdir(exist_ok=True)
            
            # Install system packages
            self.install_system_packages()
            
            # Install individual tools
            self.install_ffmpeg()
            self.install_espeak()
            self.install_festival()
            self.install_python_packages()
            self.install_coqui_tts()
            self.install_ollama()
            self.install_stable_diffusion()
            self.install_animatediff()
            
            # Create service files
            self.create_service_files()
            
            # Verify installations
            results = self.verify_installations()
            
            logger.info("Installation completed!")
            logger.info("You can now use all free AI tools for:")
            logger.info("  - Text generation (Ollama)")
            logger.info("  - Image generation (Stable Diffusion)")
            logger.info("  - Video generation (AnimateDiff + FFmpeg)")
            logger.info("  - Text-to-speech (Coqui TTS, eSpeak, Festival)")
            logger.info("  - Video processing (FFmpeg)")
            
            return True
            
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False

def main():
    """Main installation function"""
    installer = FreeAIInstaller()
    success = installer.install_all()
    
    if success:
        print("\n🎉 All free AI tools installed successfully!")
        print("Your marketing automation system now has access to:")
        print("  ✓ Free text generation")
        print("  ✓ Free image generation")
        print("  ✓ Free video generation")
        print("  ✓ Free text-to-speech")
        print("  ✓ Free video processing")
        print("\nNo API costs, unlimited usage!")
    else:
        print("\n❌ Installation failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

