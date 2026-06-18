import requests
import re
import json

def get_all_active_livestreams(channel_url):
    # Vào tab streams của kênh
    streams_url = channel_url.rstrip('/') + '/streams'
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(streams_url, headers=headers)
        response.raise_for_status()
        
        # Bóc tách cục dữ liệu JSON ytInitialData
        match = re.search(r'var ytInitialData = (\{.*?\});</script>', response.text)
        if not match:
            print("Không tìm thấy dữ liệu ytInitialData trên trang.")
            return []
            
        data = json.loads(match.group(1))
        live_streams = []
        
        def find_live_videos(node):
            if isinstance(node, list):
                for item in node:
                    find_live_videos(item)
            elif isinstance(node, dict):
                if 'videoRenderer' in node:
                    video = node['videoRenderer']
                    is_live = False
                    
                    # Kiểm tra xem video có đang live không
                    overlays = video.get('thumbnailOverlays', [])
                    for overlay in overlays:
                        time_status = overlay.get('thumbnailOverlayTimeStatusRenderer', {})
                        if time_status.get('style') == 'LIVE':
                            is_live = True
                            break
                            
                    if not is_live:
                        badges = video.get('badges', [])
                        for badge in badges:
                            badge_style = badge.get('metadataBadgeRenderer', {}).get('style')
                            if badge_style == 'BADGE_STYLE_TYPE_LIVE_NOW':
                                is_live = True
                                break
                                
                    if is_live:
                        video_id = video.get('videoId')
                        
                        # Bóc tách Tiêu đề (Title)
                        title = "Unknown Title"
                        try:
                            title = video['title']['runs'][0]['text']
                        except KeyError:
                            pass
                        
                        # Bóc tách Ảnh đại diện video (Thumbnail) để làm tvg-logo
                        logo_url = ""
                        try:
                            thumbnails = video['thumbnail']['thumbnails']
                            if thumbnails:
                                # Thường phần tử cuối cùng trong list thumbnails là ảnh chất lượng cao nhất
                                logo_url = thumbnails[-1]['url'].split('?')[0] # Bỏ các tham số tracking phía sau dấu ? nếu có
                        except KeyError:
                            pass
                            
                        if video_id:
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            live_streams.append({
                                "title": title,
                                "url": video_url,
                                "logo": logo_url
                            })
                
                # Duyệt tiếp đệ quy
                for key, value in node.items():
                    find_live_videos(value)

        find_live_videos(data)
        
        # Lọc bỏ các video bị trùng lặp (nếu JSON bị lặp data)
        unique_streams = {stream['url']: stream for stream in live_streams}.values()
        return list(unique_streams)
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
        return []

if __name__ == "__main__":
    channel = "https://www.youtube.com/@PowerRangersOfficial"
    print(f"Đang quét luồng trực tiếp trên: {channel} ...\n")
    
    streams = get_all_active_livestreams(channel)
    
    if streams:
        # Tạo chuỗi dữ liệu chuẩn M3U
        m3u_content = "#EXTM3U\n"
        for stream in streams:
            # Format đúng theo định dạng bạn yêu cầu
            m3u_content += f'#EXTINF:-1 tvg-logo="{stream["logo"]}" group-title="Youtube Live",{stream["title"]}\n'
            m3u_content += f'{stream["url"]}\n'
            
        print("Đã tạo ra dữ liệu M3U:\n")
        print(m3u_content)
        
        # Ghi ra file text
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print("\n✅ Đã lưu danh sách vào file: youtube_live.m3u")
    else:
        print("❌ Kênh hiện không có luồng trực tiếp nào.")
        # Nếu không có stream nào, lưu một file rỗng hoặc file chứa thông báo để tránh lỗi app IPTV
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n#EXTINF:-1 tvg-logo=\"\" group-title=\"Youtube Live\",Kênh hiện không có live\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ\n")
