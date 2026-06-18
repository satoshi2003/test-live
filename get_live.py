import requests
import re
import json

def get_all_active_livestreams(channel_url):
    # Vào tab streams của kênh
    streams_url = channel_url.rstrip('/') + '/streams'
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Force tiếng Anh để luôn check được chữ 'watching'
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
                # FIX LỖI: Kiểm tra nhiều loại thẻ video khác nhau thay vì chỉ 1 loại
                video_keys = ['videoRenderer', 'gridVideoRenderer', 'compactVideoRenderer', 'richItemRenderer']
                
                for key in video_keys:
                    if key in node:
                        # Xử lý trường hợp richItemRenderer bọc videoRenderer bên trong
                        if key == 'richItemRenderer' and 'content' in node[key] and 'videoRenderer' in node[key]['content']:
                            video = node[key]['content']['videoRenderer']
                        elif key != 'richItemRenderer':
                            video = node[key]
                        else:
                            continue

                        is_live = False
                        
                        # Điều kiện 1: Check qua overlay (nhãn LIVE đỏ trên ảnh)
                        for overlay in video.get('thumbnailOverlays', []):
                            time_style = overlay.get('thumbnailOverlayTimeStatusRenderer', {}).get('style', '')
                            if time_style == 'LIVE':
                                is_live = True
                                break
                                
                        # Điều kiện 2: Check qua badge ngầm
                        if not is_live:
                            for badge in video.get('badges', []):
                                badge_style = badge.get('metadataBadgeRenderer', {}).get('style', '')
                                if badge_style == 'BADGE_STYLE_TYPE_LIVE_NOW':
                                    is_live = True
                                    break
                                    
                        # Điều kiện 3 (QUAN TRỌNG NHẤT FIX LỖI GITHUB ACTIONS): 
                        # Check xem phần lượt xem có chữ "watching" không (nghĩa là đang có người xem trực tiếp)
                        if not is_live:
                            view_runs = video.get('viewCountText', {}).get('runs', [])
                            for run in view_runs:
                                text = run.get('text', '').lower()
                                if 'watching' in text or 'đang xem' in text:
                                    is_live = True
                                    break
                                    
                        if is_live:
                            video_id = video.get('videoId')
                            
                            # Bóc tách Tiêu đề (Title)
                            title = "Unknown Title"
                            try:
                                title = video['title']['runs'][0]['text']
                            except (KeyError, IndexError):
                                pass
                            
                            # Bóc tách Ảnh đại diện video (Thumbnail) để làm tvg-logo
                            logo_url = ""
                            try:
                                thumbnails = video['thumbnail']['thumbnails']
                                if thumbnails:
                                    logo_url = thumbnails[-1]['url'].split('?')[0] 
                            except (KeyError, IndexError):
                                pass
                                
                            if video_id:
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                live_streams.append({
                                    "title": title,
                                    "url": video_url,
                                    "logo": logo_url
                                })
                
                # Duyệt tiếp đệ quy
                for k, v in node.items():
                    find_live_videos(v)

        find_live_videos(data)
        
        # Lọc bỏ các video bị trùng lặp
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
        # Lưu file rỗng để không bị lỗi M3U
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
