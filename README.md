# Facebook Video Downloader

Tool tải video từ Facebook tự động với nhiều link cùng lúc.

## Yêu cầu

- Python 3.7 trở lên
- Chrome browser đã được cài đặt

## Cài đặt

1. Clone repository này về máy:
```bash
git clone <repository-url>
cd fb-video-downloader
```

2. Tạo và kích hoạt môi trường ảo:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Cách sử dụng

1. Tạo file `cookie.txt` chứa cookie Facebook của bạn
2. Tạo file `links.txt` chứa danh sách các link video Facebook (mỗi link trên một dòng)
3. Chạy script:
```bash
python downloader.py
```

## Cấu trúc file

- `downloader.py`: Script chính để tải video
- `fb_video_downloader.py`: Module chứa class FacebookDownloader
- `cookie.txt`: File chứa cookie Facebook
- `links.txt`: File chứa danh sách link video cần tải
- `download_status.json`: File lưu trạng thái tải video
- `videos/`: Thư mục chứa video đã tải
- `audio/`: Thư mục chứa audio đã tách

## Lưu ý

- Cần đăng nhập Facebook và lấy cookie để có thể tải được video private
- Tool sẽ tự động bỏ qua các video đã tải thành công trước đó
- Trạng thái tải sẽ được lưu vào file `download_status.json`
