import yt_dlp
import streamlink

def get_all_active_livestreams(channel_url):
    streams_url = channel_url.rstrip('/') + '/streams'
    
    ydl_opts = {
        'extract_flat': True, 
        'quiet': True,
        'no_warnings': True,
    }
    
    live_streams = []
    
    try:
        # BƯỚC 1: Dùng yt-dlp quét danh sách các ID đang live cực nhanh
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Đang tìm các video live trên kênh: {streams_url}")
            info = ydl.extract_info(streams_url, download=False)
            
            if 'entries' in info:
                for entry in info['entries']:
                    if entry.get('live_status') == 'is_live':
                        video_id = entry.get('id')
                        video_url = entry.get('url')
                        title = entry.get('title', 'Unknown Title')
                        logo_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault_live.jpg"
                        
                        # BƯỚC 2: Dùng sức mạnh của Streamlink để bắt link .m3u8 gốc
                        try:
                            print(f"  -> Đang bóc link m3u8 cho: {title}")
                            # Lấy các luồng stream từ url video
                            streams = streamlink.streams(video_url)
                            
                            if streams and 'best' in streams:
                                # Lấy url của chất lượng tốt nhất (thường là 1080p hoặc 720p HLS)
                                m3u8_url = streams['best'].url
                                
                                live_streams.append({
                                    "title": title,
                                    "url": m3u8_url, # Thay link youtube bằng link m3u8 xịn!
                                    "logo": logo_url
                                })
                        except Exception as e:
                            print(f"  [!] Không thể lấy m3u8 cho {video_id}: {e}")
                        
    except Exception as e:
        print(f"Lỗi hệ thống quét yt-dlp: {e}")
        
    return live_streams

if __name__ == "__main__":
    channel = "https://www.youtube.com/@PowerRangersOfficial"
    print(f"Bắt đầu quy trình tạo M3U8 cho kênh: {channel} ...\n")
    
    streams = get_all_active_livestreams(channel)
    
    if streams:
        m3u_content = "#EXTM3U\n"
        for stream in streams:
            m3u_content += f'#EXTINF:-1 tvg-logo="{stream["logo"]}" group-title="Youtube Live",{stream["title"]}\n'
            # Link dưới đây sẽ là một đoạn m3u8 siêu dài của máy chủ Google
            m3u_content += f'{stream["url"]}\n'
            
        print(f"\n✅ Đã bóc thành công {len(streams)} luồng m3u8 gốc!")
        
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print("✅ Đã lưu danh sách vào file: youtube_live.m3u")
    else:
        print("❌ Kênh hiện không có luồng trực tiếp nào.")
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
