import requests
import re
import json

def get_live_videos(channel_url):
    streams_url = channel_url.rstrip('/') + '/streams'
    
    # Gửi kèm Cookie CONSENT=YES để đi xuyên qua màn hình chặn của Google
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": "CONSENT=YES+cb.20210328-17-p0.en+FX+113" 
    }
    
    try:
        print(f"Đang lấy dữ liệu từ: {streams_url}")
        response = requests.get(streams_url, headers=headers)
        response.raise_for_status()
        
        match = re.search(r'var ytInitialData = (\{.*?\});</script>', response.text)
        if not match:
            print("❌ Bị chặn hoặc không tìm thấy dữ liệu.")
            return []
            
        data = json.loads(match.group(1))
        live_streams = []
        
        def find_live_videos(node):
            if isinstance(node, list):
                for item in node:
                    find_live_videos(item)
            elif isinstance(node, dict):
                for key in ['videoRenderer', 'gridVideoRenderer', 'compactVideoRenderer', 'richItemRenderer']:
                    if key in node:
                        if key == 'richItemRenderer' and 'content' in node[key] and 'videoRenderer' in node[key]['content']:
                            video = node[key]['content']['videoRenderer']
                        elif key != 'richItemRenderer':
                            video = node[key]
                        else:
                            continue

                        is_live = False
                        
                        # Check nhãn LIVE
                        for badge in video.get('badges', []):
                            if badge.get('metadataBadgeRenderer', {}).get('style') == 'BADGE_STYLE_TYPE_LIVE_NOW':
                                is_live = True
                                break
                        
                        # Check chữ watching
                        if not is_live:
                            for run in video.get('viewCountText', {}).get('runs', []):
                                text = run.get('text', '').lower()
                                if 'watching' in text or 'đang xem' in text:
                                    is_live = True
                                    break

                        if is_live:
                            video_id = video.get('videoId')
                            title = "Unknown Title"
                            try:
                                title = video['title']['runs'][0]['text']
                            except Exception:
                                pass
                                
                            if video_id:
                                live_streams.append({
                                    "id": video_id,
                                    "title": title,
                                    # TRẢ VỀ LINK GỐC NHƯ BẠN YÊU CẦU
                                    "url": f"https://www.youtube.com/watch?v={video_id}",
                                    "logo": f"https://i.ytimg.com/vi/{video_id}/hqdefault_live.jpg"
                                })
                
                for k, v in node.items():
                    find_live_videos(v)

        find_live_videos(data)
        
        # Lọc ID trùng lặp
        unique_streams = {s['id']: s for s in live_streams}.values()
        return list(unique_streams)
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
        return []

if __name__ == "__main__":
    channel = "https://www.youtube.com/@PowerRangersOfficial"
    print(f"Bắt đầu quy trình quét kênh: {channel} ...\n")
    
    streams = get_live_videos(channel)
    
    if streams:
        m3u_content = "#EXTM3U\n"
        for stream in streams:
            m3u_content += f'#EXTINF:-1 tvg-logo="{stream["logo"]}" group-title="Youtube Live",{stream["title"]}\n'
            m3u_content += f'{stream["url"]}\n'
            
        print(f"🎉 Phát hiện {len(streams)} luồng đang LIVE!")
        print(m3u_content)
        
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print("✅ Đã lưu danh sách vào file: youtube_live.m3u")
    else:
        print("❌ Kênh hiện không có luồng trực tiếp nào hoặc bị chặn.")
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
