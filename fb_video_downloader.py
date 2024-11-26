import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import requests
import os
import json

class FacebookDownloader:
    def __init__(self, cookie_file):
        self.cookie_file = cookie_file
        self.status_file = 'download_status.json'
        self.download_status = self.load_download_status()
        self.setup_driver()
        
    def load_download_status(self):
        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"completed": [], "failed": [], "last_index": 0}

    def save_download_status(self):
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.download_status, f, ensure_ascii=False, indent=4, sort_keys=True)

    def is_completed(self, link):
        return link in self.download_status["completed"]

    def add_completed(self, link):
        if link not in self.download_status["completed"]:
            self.download_status["completed"].append(link)
        self.save_download_status()

    def add_failed(self, link, error):
        failed_entry = {"link": link, "error": error}
        if failed_entry not in self.download_status["failed"]:
            self.download_status["failed"].append(failed_entry)
        self.save_download_status()

    def setup_driver(self):
        chrome_options = Options()
        
        # Thiết lập giả lập thiết bị mobile
        mobile_emulation = {
            "deviceMetrics": { "width": 360, "height": 640, "pixelRatio": 3.0 },
            "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36"
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        # Các tùy chọn khác
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Uncomment dòng sau nếu muốn chạy ẩn
        chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def load_cookies(self):
        try:
            # Truy cập m.facebook.com thay vì facebook.com
            self.driver.get("https://m.facebook.com")
            time.sleep(2)
            
            with open(self.cookie_file, 'r') as f:
                cookies = f.read().strip()
                
            for cookie in cookies.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    self.driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': '.facebook.com'
                    })
                    
            print("Đã load cookies thành công")
            
        except Exception as e:
            print(f"Lỗi khi load cookies: {str(e)}")
            
    def convert_to_mobile_url(self, url):
        """Chuyển đổi URL desktop thành mobile"""
        return url.replace('www.facebook.com', 'm.facebook.com')
            
    def get_video_url(self, url):
        try:
            print("Đang tải trang video...")
            self.load_cookies()
            
            # Extract post ID from URL
            import re
            post_id = re.search(r'/(\d+)/?$', url)
            if not post_id:
                post_id = re.search(r'/posts/(\d+)', url)
            post_id = post_id.group(1) if post_id else None
            
            # Chuyển đổi sang URL mobile
            mobile_url = self.convert_to_mobile_url(url)
            print(f"Đang truy cập URL mobile: {mobile_url}")
            
            self.driver.get(mobile_url)
            time.sleep(5)

            # Thử các phương pháp khác nhau để lấy URL video
            js_script = """
            // Tìm video trong trang mobile
            function findVideoUrl() {
                // Phương pháp 1: Tìm trực tiếp thẻ video
                let video = document.querySelector('video');
                if (video && video.src) return video.src;
                
                // Phương pháp 2: Tìm trong thẻ source
                let sources = document.querySelectorAll('video source');
                for (let source of sources) {
                    if (source.src) return source.src;
                }
                
                // Phương pháp 3: Tìm trong thẻ div có thuộc tính data-video
                let videoDiv = document.querySelector('div[data-video]');
                if (videoDiv) {
                    let dataVideo = videoDiv.getAttribute('data-video');
                    try {
                        let videoData = JSON.parse(dataVideo);
                        if (videoData.src) return videoData.src;
                    } catch(e) {}
                }
                
                // Phương pháp 4: Tìm URL trong các thẻ meta
                let videoMeta = document.querySelector('meta[property="og:video:url"]');
                if (videoMeta) return videoMeta.content;
                
                // Phương pháp 5: Tìm trong thuộc tính data-store
                let dataStoreElements = document.querySelectorAll('[data-store]');
                for (let element of dataStoreElements) {
                    try {
                        let data = JSON.parse(element.getAttribute('data-store'));
                        if (data.videoURL) return data.videoURL;
                        if (data.src) return data.src;
                    } catch(e) {}
                }
                
                return null;
            }
            return findVideoUrl();
            """
            
            # Thực thi script
            video_url = self.driver.execute_script(js_script)
            
            # Extract post content from the specific HTML structure
            post_content_script = """
            function getPostContent() {
                try {
                    // First attempt: Look for content after profile section
                    let profileSection = document.querySelector('[data-mcomponent="MContainer"][data-srat="139"]');
                    if (profileSection) {
                        let nextContainer = profileSection.nextElementSibling;
                        if (nextContainer) {
                            let nativeText = nextContainer.querySelector('.native-text');
                            if (nativeText) {
                                let content = nativeText.textContent.trim();
                                if (content && content.length > 10) {
                                    return cleanContent(content);
                                }
                            }
                        }
                    }

                    // Second attempt: Find container with height between 20-40px containing meaningful text
                    let containers = document.querySelectorAll('[data-type="container"][data-mcomponent="MContainer"][data-actual-height]');
                    for (let container of containers) {
                        let height = parseInt(container.getAttribute('data-actual-height'));
                        if (height >= 20 && height <= 40) {
                            let nativeText = container.querySelector('.native-text');
                            if (nativeText) {
                                let content = nativeText.textContent.trim();
                                // Skip containers with common UI text
                                if (!isCommonUIText(content) && content.length > 10) {
                                    return cleanContent(content);
                                }
                            }
                        }
                    }

                    // Third attempt: Look for the longest meaningful text in a container
                    let longestContent = '';
                    containers.forEach(container => {
                        let nativeText = container.querySelector('.native-text');
                        if (nativeText) {
                            let content = nativeText.textContent.trim();
                            if (!isCommonUIText(content) && content.length > longestContent.length) {
                                longestContent = content;
                            }
                        }
                    });
                    
                    if (longestContent) {
                        return cleanContent(longestContent);
                    }

                    return '';
                } catch (e) {
                    console.error('Error in getPostContent:', e);
                    return '';
                }
            }

            function isCommonUIText(text) {
                const commonPhrases = [
                    'like', 'comment', 'share', 'reply',
                    'most relevant', 'profile picture',
                    'was live', 'others', 'top contributor'
                ];
                text = text.toLowerCase();
                return commonPhrases.some(phrase => text.includes(phrase));
            }

            function cleanContent(content) {
                return content
                    .replace(/[\\n\\r]+/g, ' ')  // Replace newlines with space
                    .replace(/[<>:"/\\|?*]/g, '_')  // Replace invalid filename characters with underscore
                    .trim()  // Remove leading/trailing spaces
                    // Capitalize first letter of each word and preserve dots
                    .split(/\\s+/)
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join('_')
                    .substring(0, 150)  // Limit length
                    .replace(/_+/g, '_')  // Replace multiple underscores with single one
                    .replace(/^_+|_+$/g, '');  // Remove leading/trailing underscores
            }

            return getPostContent();
            """
            
            # Thực thi script
            post_content = self.driver.execute_script(post_content_script)
            
            if not video_url:
                print("Thử tìm trong page source...")
                # Tìm trong page source
                page_source = self.driver.page_source
                import re
                patterns = [
                    r'videoURL":"([^"]+)"',
                    r'video_url":"([^"]+)"',
                    r'playable_url":"([^"]+)"',
                    r'playable_url_quality_hd":"([^"]+)"',
                    r'<video[^>]+src="([^"]+)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        video_url = match.group(1).replace('\\/', '/')
                        break
            
            if video_url:
                print("Đã tìm thấy URL video:", video_url)
                return {
                    'status': 'success',
                    'url': video_url,
                    'content': post_content,
                    'post_id': post_id
                }
            else:
                # Lưu screenshot để debug
                self.driver.save_screenshot("debug/debug_screenshot.png")
                return {
                    'status': 'error',
                    'message': 'Không tìm thấy URL video'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Lỗi khi lấy URL video: {str(e)}'
            }
        
    def download_video(self, video_url, output_path):
        try:
            session = requests.Session()
            
            # Copy cookies từ selenium sang requests
            for cookie in self.driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
                
            # Headers giả lập mobile
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Range': 'bytes=0-',
                'Referer': 'https://m.facebook.com/',
                'Origin': 'https://m.facebook.com'
            }
            
            print(f"Bắt đầu tải video...")
            response = session.get(video_url, headers=headers, stream=True)
            
            if response.status_code in [200, 206]:
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"\rTải xuống: {percent:.1f}%", end='')
                
                print("\nHoàn thành!")
                return {
                    'status': 'success',
                    'message': f'Video đã được tải về: {output_path}'
                }
            return {
                'status': 'error',
                'message': f'Không thể tải video. Status code: {response.status_code}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Lỗi khi tải video: {str(e)}'
            }
            
    def download_videos(self):
        try:
            # Đọc danh sách link từ file
            with open('video_links.txt', 'r') as f:
                links = [line.strip() for line in f if line.strip()]

            for i, link in enumerate(links[self.download_status["last_index"]:], self.download_status["last_index"]):
                try:
                    # Skip if already completed
                    if self.is_completed(link):
                        print(f"Skipping {link} - already completed")
                        continue

                    print(f"\nProcessing link {i + 1}/{len(links)}: {link}")
                    
                    # Lấy thông tin video
                    video_info = self.get_video_url(link)
                    
                    if video_info['status'] == 'success':
                        # Use post content or post ID for filename
                        filename = video_info['content'] if video_info['content'] else video_info['post_id']
                        if not filename:
                            filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        
                        output_file = f"{filename}.mp4"
                        result = self.download_video(video_info['url'], output_file)
                        print(result['message'])
                        self.add_completed(link)
                    else:
                        print(f"Lỗi: {video_info['message']}")
                        self.add_failed(link, video_info['message'])
                    
                    # Update last processed index
                    self.download_status["last_index"] = i + 1
                    self.save_download_status()

                except Exception as e:
                    print(f"Error processing {link}: {str(e)}")
                    self.add_failed(link, str(e))
                    continue

        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    cookie_file = "cookie.txt"
    
    try:
        downloader = FacebookDownloader(cookie_file)
        
        downloader.download_videos()

    except Exception as e:
        print(f"Lỗi: {str(e)}")
        
    finally:
        downloader.close()

if __name__ == "__main__":
    main()