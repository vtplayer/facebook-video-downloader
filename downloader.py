import json
import os
from datetime import datetime
from fb_video_downloader import FacebookDownloader  # Class từ file trước

class BatchVideoDownloader:
    def __init__(self, cookie_file):
        self.cookie_file = cookie_file
        self.downloader = FacebookDownloader(cookie_file)
        self.download_status = self.load_download_status()
        
    def load_download_status(self):
        """Load trạng thái download từ file"""
        try:
            with open('download_status.json', 'r') as f:
                return json.load(f)
        except:
            return {'completed': [], 'failed': [], 'last_index': 0}
            
    def save_download_status(self):
        """Lưu trạng thái download"""
        with open('download_status.json', 'w', encoding='utf-8') as f:
            json.dump(self.download_status, f, ensure_ascii=False, indent=4)
            
    def process_links(self, links_file):
        """Xử lý danh sách links"""
        try:
            with open(links_file, 'r') as f:
                links = f.read().splitlines()
                
            start_index = self.download_status['last_index']
            print(f"Tiếp tục từ index: {start_index}")
            
            for i, link in enumerate(links[start_index:], start=start_index):
                try:
                    if link in self.download_status['completed']:
                        print(f"Đã tải trước đó: {link}")
                        continue
                        
                    print(f"\nĐang xử lý link {i+1}/{len(links)}: {link}")
                    
                    video_info = self.downloader.get_video_url(link)
                    
                    if video_info['status'] == 'success':
                        post_content = video_info.get('content', 'video')
                        sanitized_content = ''.join(e for e in post_content if e.isalnum() or e.isspace()).strip().replace(' ', '_')
                        output_file = f"videos/{sanitized_content}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                        
                        os.makedirs('videos', exist_ok=True)
                        
                        result = self.downloader.download_video(video_info['url'], output_file)
                        
                        if result['status'] == 'success':
                            self.download_status['completed'].append(link)
                            print(f"Đã tải thành công: {output_file}")
                        else:
                            self.download_status['failed'].append({
                                'link': link,
                                'error': result['message']
                            })
                            print(f"Lỗi khi tải: {result['message']}")
                    else:
                        self.download_status['failed'].append({
                            'link': link,
                            'error': video_info['message']
                        })
                        print(f"Lỗi khi lấy thông tin video: {video_info['message']}")
                        
                except Exception as e:
                    print(f"Lỗi khi xử lý link {link}: {str(e)}")
                    self.download_status['failed'].append({
                        'link': link,
                        'error': str(e)
                    })
                
                self.download_status['last_index'] = i
                self.save_download_status()
                
        except Exception as e:
            print(f"Lỗi trong quá trình xử lý batch: {str(e)}")
        finally:
            self.downloader.close()
            
        print("\nKết quả:")
        print(f"Tổng số links: {len(links)}")
        print(f"Đã tải thành công: {len(self.download_status['completed'])}")
        print(f"Thất bại: {len(self.download_status['failed'])}")
        
        if self.download_status['failed']:
            with open('failed_links.txt', 'w', encoding='utf-8') as f:
                for fail in self.download_status['failed']:
                    f.write(f"{fail['link']} - Error: {fail['error']}\n")
            print("Danh sách links thất bại đã được lưu vào failed_links.txt")

def main():
    cookie_file = "cookie.txt"
    links_file = "video_links.txt"
    
    downloader = BatchVideoDownloader(cookie_file)
    downloader.process_links(links_file)

if __name__ == "__main__":
    main()