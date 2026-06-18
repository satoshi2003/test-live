import requests
import re
import json
import streamlink

def get_live_videos_with_cookie(channel_url):
    streams_url = channel_url.rstrip('/') + '/streams'
    
    # BÍ QUYẾT VƯỢT RÀO: Gửi kèm Cookie CONSENT=YES để Google không chặn IP của Github Actions
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": "CONSENT=YES+cb.20210328-17-p0.en+FX+113" 
    }
    
    try:
        print(f"Đang vượt rào Google để lấy dữ liệu từ: {streams_url}")
        response = requests.get(streams_url, headers=headers)
        response.raise_for_status()
        
        # Bóc tách cục dữ liệu JSON ytInitialData
        match = re.search(r'var ytInitialData = (\{.*?\});</script>', response.text)
        if not match:
            print("❌ Bị chặn hoặc không tìm thấy dữ liệu (ytInitialData).")
            return []
            
        data = json.loads(match.group(1))
        live_ids = []
        
        # Thuật toán cào Video ID đang live
        def find_live_videos(node):
            if isinstance(node, list):
                for item in node:
                    find_live_videos(item)
            elif isinstance(node, dict):
                for key in ['videoRenderer', 'gridVideoRenderer', 'compactVideoRenderer', 'richItemRenderer']:
                    if key in node:
                        # Bóc lớp vỏ richItemRenderer nếu có
                        if key == 'richItemRenderer' and 'content' in node[key] and 'videoRenderer' in node[key]['content']:
                            video = node[key]['content']['videoRenderer']
                        elif key != 'richItemRenderer':
                            video = node[key]
                        else:
                            continue

                        is_live = False
                        
                        # Điều kiện 1: Nhãn badge "Đang trực tiếp"
                        for badge in video.get('badges', []):
                            if badge.get('metadataBadgeRenderer', {}).get('style') == 'BADGE_STYLE_TYPE_LIVE_NOW':
                                is_live = True
                                break
                        
                        # Điều kiện 2: Lượt xem có chữ "watching"
                        if not is_live:
                            for run in video.get('viewCountText', {}).get('runs', []):
                                if 'watching' in run.get('text', '').lower() or 'đang xem' in run.get('text', '').lower():
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
                                live_ids.append({"id": video_id, "title": title})
                
                # Tiếp tục đệ quy
                for k, v in node.items():
                    find_live_videos(v)

        find_live_videos(data)
        
        # Lọc ID trùng lặp
        unique_vids = {v['id']: v for v in live_ids}.values()
        
        # BƯỚC 2: Dùng Streamlink để lấy link M3U8 từ các ID vừa tìm được
        final_streams = []
        for vid in unique_vids:
            vid_url = f"https://www.youtube.com/watch?v={vid['id']}"
            print(f"✅ Phát hiện LIVE: {vid['title']}")
            print(f"  -> Đang dùng Streamlink bóc M3U8...")
            
            try:
                # Bắt luồng HLS trực tiếp
                streams = streamlink.streams(vid_url)
                if streams and 'best' in streams:
                    m3u8_url = streams['best'].url
                    logo = f"https://i.ytimg.com/vi/{vid['id']}/hqdefault_live.jpg"
                    
                    final_streams.append({
                        "title": vid['title'],
                        "url": m3u8_url,
                        "logo": logo
                    })
                    print("  -> Lấy link M3U8 thành công!")
                else:
                    print("  -> Không tìm thấy luồng best.")
            except Exception as e:
                print(f"  -> [LỖI] Không thể bóc link: {e}")
                
        return final_streams
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
        return []

if __name__ == "__main__":
    channel = "https://www.youtube.com/@PowerRangersOfficial"
    print(f"Bắt đầu quy trình quét kênh: {channel} ...\n")
    
    streams = get_live_videos_with_cookie(channel)
    
    if streams:
        m3u_content = "#EXTM3U\n"
        for stream in streams:
            m3u_content += f'#EXTINF:-1 tvg-logo="{stream["logo"]}" group-title="Youtube Live",{stream["title"]}\n'
            m3u_content += f'{stream["url"]}\n'
            
        print(f"\n🎉 HOÀN TẤT! Đã bóc thành công {len(streams)} luồng m3u8 gốc!")
        
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print("✅ Đã lưu danh sách vào file: youtube_live.m3u")
    else:
        print("\n❌ Kênh hiện không có luồng trực tiếp nào hoặc bị chặn.")
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
