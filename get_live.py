from playwright.sync_api import sync_playwright
import time
import re

def get_all_active_livestreams(channel_url):
    streams_url = channel_url.rstrip('/') + '/streams'
    live_streams = []

    print("Khởi động trình duyệt ảo...")
    with sync_playwright() as p:
        # Mở Chrome chế độ ẩn (headless)
        browser = p.chromium.launch(headless=True)
        # Bắt buộc ngôn ngữ tiếng Anh để dễ bắt chữ "watching"
        page = browser.new_page(locale="en-US")
        
        try:
            print(f"Đang truy cập: {streams_url}")
            page.goto(streams_url, wait_until="networkidle")
            
            # Cuộn chuột xuống một chút để YouTube nạp (render) video
            page.mouse.wheel(0, 1000)
            time.sleep(3) # Chờ 3 giây cho dữ liệu load hẳn
            
            # Quét tất cả các thẻ chứa video trên màn hình
            videos = page.locator('ytd-rich-grid-media').all()
            
            for vid in videos:
                text_content = vid.inner_text().lower()
                
                # Nếu video có chữ "watching" nghĩa là ĐANG TRỰC TIẾP
                if "watching" in text_content:
                    # Lấy Tiêu đề
                    title_el = vid.locator('#video-title')
                    title = title_el.inner_text() if title_el.count() > 0 else "Unknown Title"
                    
                    # Lấy Link
                    link_el = vid.locator('a#thumbnail')
                    url = "https://www.youtube.com" + link_el.get_attribute('href') if link_el.count() > 0 else ""
                    
                    if url:
                        # Bóc tách Video ID từ link (VD: watch?v=ABCXYZ)
                        video_id_match = re.search(r'v=([a-zA-Z0-9_-]+)', url)
                        if video_id_match:
                            video_id = video_id_match.group(1)
                            # Tự động gen link ảnh đại diện nét nhất từ server YouTube (không sợ bị lỗi ảnh mờ)
                            logo_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault_live.jpg"
                            
                            live_streams.append({
                                "title": title,
                                "url": url,
                                "logo": logo_url
                            })
                            
        except Exception as e:
            print(f"Lỗi trong quá trình quét trình duyệt: {e}")
        finally:
            browser.close()
            
    # Lọc các link trùng lặp (nếu có)
    unique_streams = {stream['url']: stream for stream in live_streams}.values()
    return list(unique_streams)

if __name__ == "__main__":
    channel = "https://www.youtube.com/@PowerRangersOfficial"
    print(f"Đang quét luồng trực tiếp trên: {channel} ...\n")
    
    streams = get_all_active_livestreams(channel)
    
    if streams:
        m3u_content = "#EXTM3U\n"
        for stream in streams:
            m3u_content += f'#EXTINF:-1 tvg-logo="{stream["logo"]}" group-title="Youtube Live",{stream["title"]}\n'
            m3u_content += f'{stream["url"]}\n'
            
        print(f"✅ Đã tìm thấy {len(streams)} luồng LIVE!\n")
        print(m3u_content)
        
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print("\n✅ Đã lưu danh sách vào file: youtube_live.m3u")
    else:
        print("❌ Kênh hiện không có luồng trực tiếp nào.")
        # Lưu file rỗng để không bị lỗi ứng dụng M3U
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n#EXTINF:-1 tvg-logo=\"\" group-title=\"Youtube Live\",Kênh hiện không có live\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ\n")
