import yt_dlp

def get_all_active_livestreams(channel_url):
    # Truy cập vào tab streams
    streams_url = channel_url.rstrip('/') + '/streams'
    
    # Cấu hình yt-dlp
    ydl_opts = {
        'extract_flat': True, # Chỉ lấy danh sách, không tải video (rất nhanh)
        'quiet': True,        # Ẩn log của yt-dlp cho đỡ rác màn hình
        'no_warnings': True,
    }
    
    live_streams = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Đang dùng yt-dlp bóc tách dữ liệu từ: {streams_url}")
            # Lấy toàn bộ thông tin các video trong tab streams
            info = ydl.extract_info(streams_url, download=False)
            
            if 'entries' in info:
                for entry in info['entries']:
                    # yt-dlp có sẵn bộ lọc cực thông minh, trả về 'is_live' nếu video đang phát trực tiếp
                    if entry.get('live_status') == 'is_live':
                        video_id = entry.get('id')
                        title = entry.get('title', 'Unknown Title')
                        url = entry.get('url')
                        logo_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault_live.jpg"
                        
                        live_streams.append({
                            "title": title,
                            "url": url,
                            "logo": logo_url
                        })
                        
    except Exception as e:
        print(f"Lỗi trong quá trình quét yt-dlp: {e}")
        
    return live_streams

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
        with open("youtube_live.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n#EXTINF:-1 tvg-logo=\"\" group-title=\"Youtube Live\",Kênh hiện không có live\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ\n")
