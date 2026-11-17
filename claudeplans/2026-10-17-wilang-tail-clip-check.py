#!/usr/bin/env python3
"""Do Wilang's last-sentence clips include the untranscribed tail of the video? (read-only, 2026-10-17)

Run on the Mac (the container cannot reach Hugging Face), from anywhere:

    python3 claudeplans/2026-10-17-wilang-tail-clip-check.py

For each of the 23 videos that have an _untranscribed companion, reads the first 4 KB (the WAV header) of the
last sentence's clip and of the companion clip from FormosanBank/YutasWilang at the pinned revision, and prints
each clip's duration. Nothing is downloaded in full. Standard library only.

If a last-sentence clip lasts about as long as the companion's tail span, it contains the untranscribed tail
(the XML gives the last sentence no end time); if it lasts a few seconds, the clip stops where the caption does.
"""
import struct, sys, urllib.request

REPO = "https://huggingface.co/datasets/FormosanBank/YutasWilang/resolve/84f9ff90ad4d92b136c14f143e5184549cdb1cdb/Atayal/"
# video stem, last sentence's clip, its start (s), companion clip, companion span(s) in the first published version (e4bb1b5ba)
ROWS = [
    ('20180723_fangwenYutas_Wilan_02buluolingxiu', '20180723_fangwenYutas_Wilan_02buluolingxiu_Atayal_3.wav', '6.74', '20180723_fangwenYutas_Wilan_02buluolingxiu_untranscribed.wav', '14.460-266.333'),
    ('20180723_fangwenYutas_Wilan_03', '20180723_fangwenYutas_Wilan_03_Atayal_4.wav', '14.48', '20180723_fangwenYutas_Wilan_03_untranscribed.wav', '21.340-1413.933'),
    ('20180723_fangwenYutas_Wilang_12_Halus_jurenhalusidegushi', '20180723_fangwenYutas_Wilang_12_Halus_jurenhalusidegushi_Atayal_23.wav', '79.7', '20180723_fangwenYutas_Wilang_12_Halus_jurenhalusidegushi_untranscribed.wav', '83.700-239.026'),
    ('20180728_Yutas_Wilang_MVI_1081_zuyuzimuyiwanchengdaotianxiangxibaotiqin', '20180728_Yutas_Wilang_MVI_1081_zuyuzimuyiwanchengdaotianxiangxibaotiqin_Atayal_37.wav', '142.565', '20180728_Yutas_Wilang_MVI_1081_zuyuzimuyiwanchengdaotianxiangxibaotiqin_untranscribed.wav', '144.085-145.705'),
    ('20180728_Yutas_Wilang_MVI_1085_yifen32miao', '20180728_Yutas_Wilang_MVI_1085_yifen32miao_Atayal_18.wav', '88.82', '20180728_Yutas_Wilang_MVI_1085_yifen32miao_untranscribed.wav', '0.000-2.340 93.100-313.377'),
    ('20180804_Yutas_Wilang_MVI_1114', '20180804_Yutas_Wilang_MVI_1114_Atayal_8.wav', '18.863', '20180804_Yutas_Wilang_MVI_1114_untranscribed.wav', '29.680-470.529'),
    ('20180804_Yutas_Wilang_MVI_1115_mengzhan_2fen14miao', '20180804_Yutas_Wilang_MVI_1115_mengzhan_2fen14miao_Atayal_35.wav', '134.54', '20180804_Yutas_Wilang_MVI_1115_mengzhan_2fen14miao_untranscribed.wav', '141.100-565.127'),
    ('20181228_yutasWilang_01_kinhulan_zuyuzimuwancheng', '20181228_yutasWilang_01_kinhulan_zuyuzimuwancheng_Atayal_584.wav', '2174.86', '20181228_yutasWilang_01_kinhulan_zuyuzimuwancheng_untranscribed.wav', '0.000-2.720'),
    ('20181228_yutasWilang_02_laqiCipuq', '20181228_yutasWilang_02_laqiCipuq_Atayal_40.wav', '228.28', '20181228_yutasWilang_02_laqiCipuq_untranscribed.wav', '0.000-1.300 231.595-2096.715'),
    ('20181228_yutasWilang_03tanlunyouguanluanlun', '20181228_yutasWilang_03tanlunyouguanluanlun_Atayal_43.wav', '180.54', '20181228_yutasWilang_03tanlunyouguanluanlun_untranscribed.wav', '183.240-184.808'),
    ('20190130_YutasWilang_dierduan_19fen7miao', '20190130_YutasWilang_dierduan_19fen7miao_Atayal_337.wav', '1436.66', '20190130_YutasWilang_dierduan_19fen7miao_untranscribed.wav', '1443.040-2078.151'),
    ('20190130_YutasWilang_diyiduan_ribenbing_6fen18miao', '20190130_YutasWilang_diyiduan_ribenbing_6fen18miao_Atayal_104.wav', '406.2', '20190130_YutasWilang_diyiduan_ribenbing_6fen18miao_untranscribed.wav', '413.720-2083.178'),
    ('20190209_YutasWilang_ki_Yagu_02_dierduan', '20190209_YutasWilang_ki_Yagu_02_dierduan_Atayal_32.wav', '145.085', '20190209_YutasWilang_ki_Yagu_02_dierduan_untranscribed.wav', '148.300-1635.114'),
    ('20190209_YutasWilang_ki_Yagu_03_disanduan', '20190209_YutasWilang_ki_Yagu_03_disanduan_Atayal_9.wav', '43.32', '20190209_YutasWilang_ki_Yagu_03_disanduan_untranscribed.wav', '45.620-509.771'),
    ('20190209_YutasWilang_ki_Yagu_07_diqiduan_yakidege', '20190209_YutasWilang_ki_Yagu_07_diqiduan_yakidege_Atayal_14.wav', '90.28', '20190209_YutasWilang_ki_Yagu_07_diqiduan_yakidege_untranscribed.wav', '95.920-203.964'),
    ('20190209_YutasWilang_ki_Yagu_10_dishiduan_daobie', '20190209_YutasWilang_ki_Yagu_10_dishiduan_daobie_Atayal_15.wav', '80.14', '20190209_YutasWilang_ki_Yagu_10_dishiduan_daobie_untranscribed.wav', '0.000-1.580'),
    ('20190407_Yutas_Wilang_di1duan_Sayun_MVI_1699', '20190407_Yutas_Wilang_di1duan_Sayun_MVI_1699_Atayal_73.wav', '492.9', '20190407_Yutas_Wilang_di1duan_Sayun_MVI_1699_untranscribed.wav', '0.000-20.200'),
    ('20190407_Yutas_Wilang_di2duan_Sayun_MVI_1700', '20190407_Yutas_Wilang_di2duan_Sayun_MVI_1700_Atayal_19.wav', '113.9', '20190407_Yutas_Wilang_di2duan_Sayun_MVI_1700_untranscribed.wav', '120.040-488.548'),
    ('20190407_Yutas_Wilang_di4duan_Lowsing_Watan_MVI_1702_yiwancheng', '20190407_Yutas_Wilang_di4duan_Lowsing_Watan_MVI_1702_yiwancheng_Atayal_232.wav', '1423.34', '20190407_Yutas_Wilang_di4duan_Lowsing_Watan_MVI_1702_yiwancheng_untranscribed.wav', '0.000-2.780'),
    ('20190407_Yutas_Wilang_di5duan_Lowsing_Watan_MVI_1703', '20190407_Yutas_Wilang_di5duan_Lowsing_Watan_MVI_1703_Atayal_36.wav', '156.66', '20190407_Yutas_Wilang_di5duan_Lowsing_Watan_MVI_1703_untranscribed.wav', '163.400-176.727'),
    ('20200115_bufangwen_MVI_2303', '20200115_bufangwen_MVI_2303_Atayal_9.wav', '45.78', '20200115_bufangwen_MVI_2303_untranscribed.wav', '49.200-163.666'),
    ('20200115_bufangwen_MVI_2304', '20200115_bufangwen_MVI_2304_Atayal_52.wav', '222.1', '20200115_bufangwen_MVI_2304_untranscribed.wav', '0.000-2.580 228.220-379.890'),
    ('muqianxianzuozhepian_20160525_binkafeifangtan_Yutas_Wilang_muqianxianzuozhepian', 'muqianxianzuozhepian_20160525_binkafeifangtan_Yutas_Wilang_muqianxianzuozhepian_Atayal_682.wav', '3120.94', 'muqianxianzuozhepian_20160525_binkafeifangtan_Yutas_Wilang_muqianxianzuozhepian_untranscribed.wav', '0.000-29.860'),
]


def duration(name):
    print(f"  fetching header of {name} ...", file=sys.stderr, flush=True)
    req = urllib.request.Request(REPO + name, headers={"Range": "bytes=0-4095"})
    with urllib.request.urlopen(req, timeout=30) as r:
        head = r.read(4096)  # never more, even if the server ignores Range and sends the whole file
        cr = r.headers.get("Content-Range")
        total = int(cr.rsplit("/", 1)[1]) if cr else int(r.headers.get("Content-Length", "0"))
    if head[:4] != b"RIFF" or head[8:12] != b"WAVE":
        return f"not WAV ({head[:4]!r})"
    i, byte_rate, data_at = 12, None, None
    while i + 8 <= len(head):
        cid, size = head[i:i + 4], struct.unpack("<I", head[i + 4:i + 8])[0]
        if cid == b"fmt ":
            byte_rate = struct.unpack("<I", head[i + 16:i + 20])[0]
        if cid == b"data":
            data_at = i + 8
            break
        i += 8 + size + (size & 1)
    if not byte_rate or data_at is None:
        return "header not parsed"
    return f"{(total - data_at) / byte_rate:.2f}"


if __name__ == "__main__":
    print("video	last clip	last starts at	last clip seconds	companion seconds	companion span (first version)")
    for stem, last, start, comp, span in ROWS:
        try:
            a, b = duration(last), duration(comp)
        except Exception as e:  # report and carry on
            a = b = f"error: {e}"
        print(stem, last.rsplit("_", 1)[-1], start, a, b, span, sep="	", flush=True)
