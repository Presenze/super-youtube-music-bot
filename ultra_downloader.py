#!/usr/bin/env python3
"""
ULTRA-ROBUST DOWNLOAD SYSTEM - FUNZIONA SEMPRE!
Sistema di download con fallback multipli e anti-blocco avanzato
"""

import asyncio
import os
import logging
import subprocess
import random
import time
import json
from typing import Optional, Dict, List, Tuple
import hashlib

logger = logging.getLogger(__name__)

class UltraRobustDownloader:
    """Sistema di download ultra-robusto con fallback multipli"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]
        
        self.download_methods = [
            self._download_with_ytdlp_ultra,
            self._download_with_ytdlp_mobile,
            self._download_with_ytdlp_minimal,
            self._download_with_ytdlp_android,
            self._download_with_ytdlp_ios,
            self._download_with_ytdlp_firefox,
            self._download_with_ytdlp_edge,
            self._download_with_ytdlp_safari,
            self._download_with_ytdlp_chrome,
            self._download_with_ytdlp_basic
        ]
        
        self.cookies_file = self._find_cookies()
    
    def _find_cookies(self) -> Optional[str]:
        """Trova file cookies disponibili"""
        possible_paths = [
            "cookies.txt",
            "youtube_cookies.txt", 
            "cookies.json",
            os.path.expanduser("~/.config/youtube-dl/cookies.txt"),
            os.path.expanduser("~/.config/yt-dlp/cookies.txt"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found cookies file: {path}")
                return path
        
        return None
    
    def _get_ultra_config(self, format_type: str, quality: str, output_template: str) -> Dict:
        """Configurazione ultra-potente per yt-dlp"""
        return {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_type,
                'preferredquality': quality,
            }],
            'quiet': True,
            'no_warnings': True,
            'writethumbnail': True,
            'embed_thumbnail': True,
            'add_metadata': True,
            'user_agent': random.choice(self.user_agents),
            'extractor_retries': 5,
            'fragment_retries': 5,
            'retries': 5,
            'socket_timeout': 60,
            'http_chunk_size': 10485760,  # 10MB
            'sleep_interval': 1,
            'max_sleep_interval': 3,
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,it;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            },
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['configs'],
                    'max_comments': [0],
                    'include_live_chat': False,
                    'player_client': ['android', 'web'],
                }
            },
            'cookiefile': self.cookies_file if self.cookies_file else None
        }
    
    def _get_mobile_config(self, format_type: str, quality: str, output_template: str) -> Dict:
        """Configurazione mobile per yt-dlp"""
        return {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_type,
                'preferredquality': quality,
            }],
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
            'extractor_retries': 3,
            'fragment_retries': 3,
            'retries': 3,
            'socket_timeout': 30,
            'sleep_interval': 0.5,
            'max_sleep_interval': 2,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                }
            },
            'cookiefile': self.cookies_file if self.cookies_file else None
        }
    
    def _get_minimal_config(self, format_type: str, quality: str, output_template: str) -> Dict:
        """Configurazione minima per yt-dlp"""
        return {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_type,
                'preferredquality': quality,
            }],
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'extractor_retries': 1,
            'fragment_retries': 1,
            'retries': 1,
            'sleep_interval': 0,
            'max_sleep_interval': 0,
            'socket_timeout': 10,
            'cookiefile': self.cookies_file if self.cookies_file else None
        }
    
    async def _download_with_ytdlp_ultra(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con configurazione ultra-potente"""
        try:
            import yt_dlp
            config = self._get_ultra_config(format_type, quality, output_template)
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Ultra config failed: {e}")
            return False
    
    async def _download_with_ytdlp_mobile(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con configurazione mobile"""
        try:
            import yt_dlp
            config = self._get_mobile_config(format_type, quality, output_template)
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Mobile config failed: {e}")
            return False
    
    async def _download_with_ytdlp_minimal(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con configurazione minima"""
        try:
            import yt_dlp
            config = self._get_minimal_config(format_type, quality, output_template)
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Minimal config failed: {e}")
            return False
    
    async def _download_with_ytdlp_android(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con user agent Android"""
        try:
            import yt_dlp
            config = self._get_minimal_config(format_type, quality, output_template)
            config['user_agent'] = 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'
            config['extractor_args'] = {'youtube': {'player_client': ['android']}}
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Android config failed: {e}")
            return False
    
    async def _download_with_ytdlp_ios(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con user agent iOS"""
        try:
            import yt_dlp
            config = self._get_minimal_config(format_type, quality, output_template)
            config['user_agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
            config['extractor_args'] = {'youtube': {'player_client': ['ios']}}
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"iOS config failed: {e}")
            return False
    
    async def _download_with_ytdlp_firefox(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con user agent Firefox"""
        try:
            import yt_dlp
            config = self._get_minimal_config(format_type, quality, output_template)
            config['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Firefox config failed: {e}")
            return False
    
    async def _download_with_ytdlp_edge(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con user agent Edge"""
        try:
            import yt_dlp
            config = self._get_minimal_config(format_type, quality, output_template)
            config['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0 Safari/537.36'
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Edge config failed: {e}")
            return False
    
    async def _download_with_ytdlp_safari(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con user agent Safari"""
        try:
            import yt_dlp
            config = self._get_minimal_config(format_type, quality, output_template)
            config['user_agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15'
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Safari config failed: {e}")
            return False
    
    async def _download_with_ytdlp_chrome(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con user agent Chrome"""
        try:
            import yt_dlp
            config = self._get_minimal_config(format_type, quality, output_template)
            config['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Chrome config failed: {e}")
            return False
    
    async def _download_with_ytdlp_basic(self, url: str, format_type: str, quality: str, output_template: str) -> bool:
        """Download con configurazione ultra-basica"""
        try:
            import yt_dlp
            config = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format_type,
                    'preferredquality': quality,
                }],
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'no_check_certificate': True,
                'extractor_retries': 0,
                'fragment_retries': 0,
                'retries': 0,
                'sleep_interval': 0,
                'max_sleep_interval': 0,
                'socket_timeout': 5,
            }
            with yt_dlp.YoutubeDL(config) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            logger.warning(f"Basic config failed: {e}")
            return False
    
    async def download_audio_ultra_robust(self, url: str, user_id: int, format_type: str = 'mp3', quality: str = '320') -> Tuple[Optional[str], Optional[Dict]]:
        """Download audio con sistema ultra-robusto - FUNZIONA SEMPRE!"""
        logger.info(f"🚀 Starting ULTRA-ROBUST download for user {user_id}: {format_type} {quality}k")
        
        try:
            # Crea directory utente
            user_dir = os.path.join("downloads", str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            # Template output
            output_template = os.path.join(user_dir, f"%(title)s.%(ext)s")
            
            # Prova tutti i metodi di download
            for i, method in enumerate(self.download_methods):
                try:
                    logger.info(f"🔄 Trying download method {i+1}/{len(self.download_methods)}")
                    
                    # Esegui download
                    success = await method(url, format_type, quality, output_template)
                    
                    if success:
                        logger.info(f"✅ Download successful with method {i+1}")
                        
                        # Trova il file scaricato
                        for file in os.listdir(user_dir):
                            if file.endswith(f'.{format_type}'):
                                file_path = os.path.join(user_dir, file)
                                file_size = os.path.getsize(file_path)
                                
                                # Controlla dimensione file
                                if file_size > 100 * 1024 * 1024:  # 100MB
                                    os.remove(file_path)
                                    continue
                                
                                # Ottieni info video
                                try:
                                    import yt_dlp
                                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                                        info = ydl.extract_info(url, download=False)
                                        video_info = {
                                            'title': info.get('title', 'Unknown'),
                                            'uploader': info.get('uploader', 'Unknown'),
                                            'duration': info.get('duration', 0),
                                            'webpage_url': info.get('webpage_url', url)
                                        }
                                except:
                                    video_info = {
                                        'title': file.replace(f'.{format_type}', ''),
                                        'uploader': 'Unknown',
                                        'duration': 0,
                                        'webpage_url': url
                                    }
                                
                                logger.info(f"🎉 ULTRA-ROBUST download completed successfully!")
                                return file_path, video_info
                    
                except Exception as e:
                    logger.warning(f"Method {i+1} failed: {e}")
                    continue
            
            # Se tutti i metodi falliscono
            logger.error("❌ All download methods failed")
            return None, "All download methods failed. Please try again later."
            
        except Exception as e:
            logger.error(f"Ultra-robust download error: {e}")
            return None, f"Download error: {str(e)}"
    
    async def get_video_info_ultra_robust(self, url: str) -> Optional[Dict]:
        """Ottieni info video con sistema ultra-robusto"""
        configs = [
            {'quiet': True, 'no_warnings': True, 'user_agent': random.choice(self.user_agents)},
            {'quiet': True, 'no_warnings': True, 'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'},
            {'quiet': True, 'no_warnings': True, 'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'},
            {'quiet': True, 'no_warnings': True, 'ignoreerrors': True, 'no_check_certificate': True},
            {'quiet': True, 'no_warnings': True, 'extract_flat': True, 'ignoreerrors': True}
        ]
        
        for i, config in enumerate(configs):
            try:
                import yt_dlp
                with yt_dlp.YoutubeDL(config) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        return {
                            'title': info.get('title', 'Unknown'),
                            'duration': info.get('duration', 0),
                            'uploader': info.get('uploader', 'Unknown'),
                            'thumbnail': info.get('thumbnail', ''),
                            'webpage_url': info.get('webpage_url', url),
                            'view_count': info.get('view_count', 0),
                            'like_count': info.get('like_count', 0),
                            'description': info.get('description', ''),
                            'upload_date': info.get('upload_date', ''),
                            'tags': info.get('tags', [])[:5] if info.get('tags') else []
                        }
            except Exception as e:
                logger.warning(f"Video info config {i+1} failed: {e}")
                continue
        
        return None
    
    async def search_youtube_ultra_robust(self, query: str, max_results: int = 10) -> List[Dict]:
        """Ricerca YouTube ultra-robusta - FUNZIONA SEMPRE!"""
        logger.info(f"🔍 Starting ULTRA-ROBUST search for: {query}")
        
        search_configs = [
            # Configurazione ultra-potente
            {
                'quiet': True,
                'no_warnings': True,
                'user_agent': random.choice(self.user_agents),
                'extractor_retries': 3,
                'fragment_retries': 3,
                'retries': 3,
                'sleep_interval': 0.5,
                'max_sleep_interval': 2,
                'socket_timeout': 30,
                'extract_flat': True,
                'ignoreerrors': True,
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash', 'hls'],
                        'player_skip': ['configs'],
                        'max_comments': [0],
                        'include_live_chat': False,
                        'player_client': ['android'],
                    }
                }
            },
            # Configurazione mobile
            {
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
                'extractor_retries': 2,
                'fragment_retries': 2,
                'retries': 2,
                'sleep_interval': 0.3,
                'max_sleep_interval': 1,
                'socket_timeout': 20,
                'extract_flat': True,
                'ignoreerrors': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                    }
                }
            },
            # Configurazione iOS
            {
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'extractor_retries': 2,
                'fragment_retries': 2,
                'retries': 2,
                'sleep_interval': 0.3,
                'max_sleep_interval': 1,
                'socket_timeout': 20,
                'extract_flat': True,
                'ignoreerrors': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios'],
                    }
                }
            },
            # Configurazione minima
            {
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'extractor_retries': 1,
                'fragment_retries': 1,
                'retries': 1,
                'sleep_interval': 0,
                'max_sleep_interval': 0,
                'socket_timeout': 10,
                'extract_flat': True,
                'ignoreerrors': True,
            },
            # Configurazione ultra-basica
            {
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'no_check_certificate': True,
                'extract_flat': True,
                'extractor_retries': 0,
                'fragment_retries': 0,
                'retries': 0,
                'sleep_interval': 0,
                'max_sleep_interval': 0,
                'socket_timeout': 5,
            }
        ]
        
        for i, config in enumerate(search_configs):
            try:
                logger.info(f"🔄 Trying search config {i+1}/{len(search_configs)}")
                
                import yt_dlp
                with yt_dlp.YoutubeDL(config) as ydl:
                    search_url = f"ytsearch{max_results}:{query}"
                    info = ydl.extract_info(search_url, download=False)
                    
                    if info and 'entries' in info:
                        results = []
                        for entry in info['entries']:
                            if entry and entry.get('id'):
                                results.append({
                                    'id': entry.get('id'),
                                    'title': entry.get('title', 'Unknown Title'),
                                    'uploader': entry.get('uploader', 'Unknown Uploader'),
                                    'duration': entry.get('duration', 0),
                                    'webpage_url': entry.get('webpage_url', f"https://youtube.com/watch?v={entry.get('id')}"),
                                    'thumbnail': entry.get('thumbnail', ''),
                                    'view_count': entry.get('view_count', 0)
                                })
                        
                        logger.info(f"✅ Search successful with config {i+1}, found {len(results)} results")
                        return results[:max_results]
                        
            except Exception as e:
                logger.warning(f"Search config {i+1} failed: {e}")
                continue
        
        logger.error("❌ All search configs failed")
        return []

# Istanza globale
ultra_downloader = UltraRobustDownloader()
