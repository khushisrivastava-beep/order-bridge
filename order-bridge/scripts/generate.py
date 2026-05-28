#!/usr/bin/env python3
"""
Order Bridge Data Generator
Usage: python generate.py <path_to_csv> [output_dir]
Outputs: d2.json and d8.json in output_dir (default: ../public/data)
The CSV must contain 8 days of data (latest day = D-1).
Columns required: placed_date, group_id, order_booking_city, sku_name,
                  order_channel_O1, order_channel, coupon_discount
"""
import csv, json, statistics, datetime, sys, os
from collections import defaultdict

def disc(val):
    try: v = float(val) if val else 0
    except: v = 0
    if v == 0: return "No Discount"
    elif v < 50: return "<\u20b950"
    elif v < 100: return "\u20b950-100"
    elif v < 200: return "\u20b9100-200"
    elif v < 500: return "\u20b9200-500"
    else: return "\u20b9500+"

def run(csv_path, out_dir):
    daily = defaultdict(set)
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            d = (row.get('placed_date') or '')[:10]
            gid = (row.get('group_id') or '').strip()
            if gid and d: daily[d].add(gid)

    dates = sorted(daily.keys())
    if len(dates) < 8:
        print(f"WARNING: only {len(dates)} dates found. Need 8 for full analysis.")
    if len(dates) > 8:
        dates = dates[-8:]  # use latest 8

    D1, D2, D8 = dates[-1], dates[-2], dates[0]
    HIST7 = dates[:-1]
    DOW = {d: datetime.date.fromisoformat(d).strftime('%A') for d in dates}
    WEEKDAY_DATES = [d for d in HIST7 if DOW[d] not in ('Saturday', 'Sunday')]
    td1, td2, td8 = len(daily[D1]), len(daily[D2]), len(daily[D8])
    tdiff_d2, tdiff_d8 = td1 - td2, td1 - td8

    print(f"D1={D1}({DOW[D1]}) D2={D2}({DOW[D2]}) D8={D8}({DOW[D8]})")
    print(f"Orders: D1={td1}  D2={td2}  D8={td8}")
    print(f"D1 vs D2: {tdiff_d2:+d} ({tdiff_d2/td2*100:+.1f}%) | D1 vs D8: {tdiff_d8:+d} ({tdiff_d8/td8*100:+.1f}%)")

    def nb(): return defaultdict(lambda: defaultdict(set))
    city_a=nb(); sku_a=nb(); cho1_a=nb(); ch_a=nb(); hr_a=nb()
    c_cho1=nb(); c_ch=nb(); c_sku=nb(); c_hr=nb()
    s_city=nb(); s_ch=nb(); s_hr=nb(); c_disc=nb(); c_dev=nb()

    with open(csv_path) as f:
        for row in csv.DictReader(f):
            d = (row.get('placed_date') or '')[:10]
            if d not in dates: continue
            gid = (row.get('group_id') or '').strip()
            if not gid: continue
            c   = (row.get('order_booking_city') or '').strip().lower()
            s   = ((row.get('sku_name') or 'Unknown').strip())[:55]
            co1 = (row.get('order_channel_O1') or 'Unknown').strip()
            ch  = (row.get('order_channel') or 'Unknown').strip()
            dt  = (row.get('device_type_o1') or row.get('device_type') or 'Unknown').strip()
            di  = disc(row.get('coupon_discount', ''))
            try: hr = int((row.get('placed_date') or '')[11:13])
            except: hr = -1
            hl = f"{hr:02d}:00" if hr >= 0 else "Unknown"
            city_a[c][d].add(gid); sku_a[s][d].add(gid)
            cho1_a[co1][d].add(gid); ch_a[ch][d].add(gid); hr_a[hl][d].add(gid)
            c_cho1[(c,co1)][d].add(gid); c_ch[(c,ch)][d].add(gid)
            c_sku[(c,s)][d].add(gid); c_hr[(c,hl)][d].add(gid)
            s_city[(s,c)][d].add(gid); s_ch[(s,co1)][d].add(gid); s_hr[(s,hl)][d].add(gid)
            c_disc[(c,di)][d].add(gid)
            if 'app' in co1.lower() or 'web' in co1.lower():
                c_dev[(c,dt)][d].add(gid)

    def cnt(v, d): return len(v.get(d, set()))
    def havg7(v):
        vals = [cnt(v, d) for d in HIST7 if cnt(v, d) > 0]
        return round(sum(vals)/len(vals), 1) if vals else 0
    def havg_wd(v):
        vals = [cnt(v, d) for d in WEEKDAY_DATES if cnt(v, d) > 0]
        return round(sum(vals)/len(vals), 1) if vals else 0

    hist7_vals = [len(daily[d]) for d in HIST7]
    hist7_avg = round(sum(hist7_vals)/len(hist7_vals), 1)
    wd_vals = [len(daily[d]) for d in WEEKDAY_DATES]
    wd_avg = round(sum(wd_vals)/len(wd_vals), 1) if wd_vals else hist7_avg
    sat_dates = [d for d in HIST7 if DOW[d] == 'Saturday']
    sun_dates = [d for d in HIST7 if DOW[d] == 'Sunday']
    sat_sun_drop = 0
    if sat_dates and sun_dates:
        sv, uv = len(daily[sat_dates[-1]]), len(daily[sun_dates[-1]])
        if sv > 0: sat_sun_drop = round((uv-sv)/sv*100, 1)

    def rec1(key, av):
        d1v=cnt(av,D1); d2v=cnt(av,D2); d8v=cnt(av,D8)
        ha7=havg7(av); ha_wd=havg_wd(av)
        hv=[cnt(av,d) for d in HIST7]
        sd_v=round(statistics.stdev(hv),1) if len([x for x in hv if x>0])>=2 else 0.
        ucl=round(ha7+sd_v,1); lcl=round(max(0,ha7-sd_v),1)
        diff_d2=d1v-d2v; diff_d8=d1v-d8v
        pct_d2=round(diff_d2/d2v*100,1) if d2v>0 else 0.
        pct_d8=round(diff_d8/d8v*100,1) if d8v>0 else 0.
        contrib_d2=round(diff_d2/tdiff_d2*100,1) if tdiff_d2!=0 else 0.
        contrib_d8=round(diff_d8/tdiff_d8*100,1) if tdiff_d8!=0 else 0.
        return {"key":key,"d1":d1v,"d2":d2v,"d8":d8v,
                "diff":diff_d2,"pct":pct_d2,"contrib":contrib_d2,
                "diff_d8":diff_d8,"pct_d8":pct_d8,"contrib_d8":contrib_d8,
                "hist_avg":ha7,"hist_avg_wd":ha_wd,"hist_vals":hv,
                "d1_vs_hist":round((d1v-ha7)/ha7*100,1) if ha7>0 else 0.,
                "d1_vs_hist_wd":round((d1v-ha_wd)/ha_wd*100,1) if ha_wd>0 else 0.,
                "sd":sd_v,"ucl":ucl,"lcl":lcl}

    def rec2(k1,k2,av):
        r=rec1(k2,av); r["k1"]=k1; r["k2"]=k2; return r

    def s1(agg,mv=3):
        return [rec1(k,v) for k,v in agg.items() if cnt(v,D1)+cnt(v,D2)>=mv]
    def s2_abs(agg,mv=2):
        return sorted([rec2(k1,k2,v) for (k1,k2),v in agg.items() if cnt(v,D1)+cnt(v,D2)>=mv],
                      key=lambda x:-abs(x['diff']))
    def smart_limit(rows, n=10):
        g = defaultdict(list)
        for r in rows: g[r['k1']].append(r)
        out = []
        for k, rl in g.items(): rl.sort(key=lambda x:-abs(x['diff'])); out.extend(rl[:n])
        return sorted(out, key=lambda x:-abs(x['diff']))

    city_l=s1(city_a); sku_l=s1(sku_a,5); cho1_l=s1(cho1_a); ch_l=s1(ch_a,3)
    hr_l=sorted(s1(hr_a,1), key=lambda x:x['key'])

    def top(lst, key='diff', n=30):
        neg = sorted([r for r in lst if r[key]<0], key=lambda x:-abs(x[key]))[:n]
        pos = sorted([r for r in lst if r[key]>0], key=lambda x:-abs(x[key]))[:n]
        return neg, pos

    city_decl, city_gain = top(city_l); sku_decl, sku_gain = top(sku_l)
    ch_decl, ch_gain = top(ch_l, n=18)

    drill = {
        "city_cho1":smart_limit(s2_abs(c_cho1,3)),
        "city_ch":  smart_limit(s2_abs(c_ch,3)),
        "city_sku": smart_limit(s2_abs(c_sku,3),15),
        "city_hour":sorted(s2_abs(c_hr,1),key=lambda x:(x['k1'],x['k2'])),
        "sku_city": smart_limit(s2_abs(s_city,3)),
        "sku_ch":   smart_limit(s2_abs(s_ch,3)),
        "sku_hour": sorted(s2_abs(s_hr,2),key=lambda x:(x['k1'],x['k2'])),
        "city_dev": smart_limit(s2_abs(c_dev,2),8),
        "city_disc":smart_limit(s2_abs(c_disc,2),8),
    }

    base_meta = {
        "D1":D1,"D2":D2,"D8":D8,
        "D1_dow":DOW[D1],"D2_dow":DOW[D2],"D8_dow":DOW[D8],
        "total_d1":td1,"total_d2":td2,"total_d8":td8,
        "total_diff":tdiff_d2,"pct_change":round(tdiff_d2/td2*100,1),
        "total_diff_d8":tdiff_d8,"pct_change_d8":round(tdiff_d8/td8*100,1),
        "hist_avg":hist7_avg,"hist_avg_wd":wd_avg,
        "d1_vs_hist":round((td1-hist7_avg)/hist7_avg*100,1),
        "d1_vs_hist_wd":round((td1-wd_avg)/wd_avg*100,1),
        "daily":{d:len(daily[d]) for d in dates},
        "daily_dow":DOW,"hist_dates":HIST7,
        "hist_dates_wd":WEEKDAY_DATES,"sat_sun_drop":sat_sun_drop
    }

    # Anomaly detection
    def anom_d2(dim,key,av,min_v,min_m,k1=None,k2=None):
        d1v=cnt(av,D1); d2v=cnt(av,D2); d8v=cnt(av,D8)
        hv=[cnt(av,d) for d in HIST7]
        if len([x for x in hv if x>0])<3 or d1v<min_v: return None
        m=statistics.mean(hv); sd=statistics.stdev(hv)
        if sd==0 or m<min_m: return None
        ucl=m+sd; lcl=max(0,m-sd)
        if lcl<=d1v<=ucl: return None
        diff=d1v-d2v; pct=round(diff/d2v*100,1) if d2v>0 else 0
        contrib=round(diff/tdiff_d2*100,1) if tdiff_d2!=0 else 0
        diff_d8=d1v-d8v; pct_d8=round(diff_d8/d8v*100,1) if d8v>0 else 0
        contrib_d8=round(diff_d8/tdiff_d8*100,1) if tdiff_d8!=0 else 0
        sev=(d1v-ucl)/sd if d1v>ucl else (lcl-d1v)/sd
        direction='ABOVE UCL' if d1v>ucl else 'BELOW LCL'
        r={"dim":dim,"key":key,"d1":d1v,"d2":d2v,"d8":d8v,
           "mean":round(m,1),"sd":round(sd,1),"ucl":round(ucl,1),"lcl":round(lcl,1),
           "diff":diff,"pct":pct,"contrib":contrib,
           "diff_d8":diff_d8,"pct_d8":pct_d8,"contrib_d8":contrib_d8,
           "hist_vals":hv,"severity":round(abs(sev),2),"direction":direction,
           "score":round(abs(sev)*abs(contrib),2),
           "insight":f"D-1 ({d1v}) is {direction.lower()} (mean={round(m,0):.0f}, {abs(sev):.1f}\u03c3). Short-term deviation — monitor over next 2\u20133 days."}
        if k1: r['k1']=k1
        if k2: r['k2']=k2
        return r

    def anom_d8(dim,key,av,min_v,min_m,k1=None,k2=None):
        r=anom_d2(dim,key,av,min_v,min_m,k1=k1,k2=k2)
        if not r: return None
        d8v=cnt(av,D8); m=r['mean']; sd=r['sd']
        d8_dev=(d8v-m)/sd if sd>0 else 0
        if abs(d8_dev)>1.0 and abs((r['d1']-m)/sd)<abs(d8_dev): return None
        if abs(r['diff_d8'])<5: return None
        score_d8=r['severity']*abs(r['contrib_d8'])
        if score_d8<5: return None
        r['score']=round(score_d8,2)
        r['insight']=f"D-1 ({r['d1']}) is {r['direction'].lower()} (mean={round(m,0):.0f}, {r['severity']:.1f}\u03c3). Weekly change vs D-8: {r['diff_d8']:+d} ({r['pct_d8']:+.1f}%). Sustained pattern, not a D-8 outlier."
        return r

    def run_anom(fn):
        flagged=[]
        for k,v in city_a.items():
            r=fn("City",k,v,20,20); flagged.append(r) if r else None
        for k,v in sku_a.items():
            r=fn("SKU",k,v,10,10); flagged.append(r) if r else None
        for k,v in cho1_a.items():
            r=fn("Channel O1",k,v,30,30); flagged.append(r) if r else None
        for k,v in ch_a.items():
            r=fn("Channel",k,v,15,15); flagged.append(r) if r else None
        for k,v in hr_a.items():
            r=fn("Hour",k,v,20,20); flagged.append(r) if r else None
        for (k1,k2),v in c_cho1.items():
            r=fn("City \u00d7 Channel O1",f"{k1} \u00d7 {k2}",v,8,8,k1=k1,k2=k2); flagged.append(r) if r else None
        for (k1,k2),v in c_ch.items():
            r=fn("City \u00d7 Channel",f"{k1} \u00d7 {k2}",v,8,8,k1=k1,k2=k2); flagged.append(r) if r else None
        for (k1,k2),v in c_sku.items():
            r=fn("City \u00d7 SKU",f"{k1} \u00d7 {k2}",v,5,5,k1=k1,k2=k2); flagged.append(r) if r else None
        for (k1,k2),v in s_city.items():
            r=fn("SKU \u00d7 City",f"{k1} \u00d7 {k2}",v,5,5,k1=k1,k2=k2); flagged.append(r) if r else None
        for (k1,k2),v in s_ch.items():
            r=fn("SKU \u00d7 Channel",f"{k1} \u00d7 {k2}",v,5,5,k1=k1,k2=k2); flagged.append(r) if r else None
        for (k1,k2),v in c_hr.items():
            r=fn("City \u00d7 Hour",f"{k1} \u00d7 {k2}",v,5,5,k1=k1,k2=k2); flagged.append(r) if r else None
        seen=set(); deduped=[]
        for r in sorted(flagged,key=lambda x:-x['score']):
            k1s=str(r.get('k1','')).lower(); k2s=str(r.get('k2','')).lower()
            sig='|'.join(sorted([k1s,k2s,str(r['d1']),r['direction']]))
            if sig in seen: continue
            seen.add(sig); deduped.append(r)
        return deduped[:25]

    anoms_d2 = run_anom(anom_d2)
    anoms_d8 = run_anom(anom_d8)
    print(f"Anomalies: D2={len(anoms_d2)}  D8={len(anoms_d8)}")

    # Build outputs
    d2_out = {"meta":base_meta,
              "city_decl":city_decl,"city_gain":city_gain,
              "sku_decl":sku_decl,"sku_gain":sku_gain,
              "ch_o1":sorted(cho1_l,key=lambda x:-abs(x['diff'])),
              "ch_decl":ch_decl,"ch_gain":ch_gain,"hour":hr_l,
              "anomalies":anoms_d2, **drill}

    def flip(r):
        nr=dict(r); nr['d2']=r['d8']
        nr['diff']=r['diff_d8']; nr['pct']=r['pct_d8']; nr['contrib']=r['contrib_d8']
        return nr
    def fl(lst): return sorted([flip(r) for r in lst],key=lambda x:-abs(x['diff']))
    def fl2(lst): return sorted([flip(r) for r in lst],key=lambda x:-abs(x['diff']))

    all_city=fl(city_decl+city_gain); all_sku=fl(sku_decl+sku_gain)
    all_ch_o1=fl(cho1_l); all_ch=fl(ch_decl+ch_gain)
    d8_meta=dict(base_meta)
    d8_meta.update({"D2":D8,"D2_dow":DOW[D8],"total_d2":td8,
                    "total_diff":tdiff_d8,"pct_change":round(tdiff_d8/td8*100,1),"label_d2":"D-8"})
    d8_out = {"meta":d8_meta,
              "city_decl":sorted([r for r in all_city if r['diff']<0],key=lambda x:-abs(x['diff']))[:30],
              "city_gain":sorted([r for r in all_city if r['diff']>0],key=lambda x:-abs(x['diff']))[:25],
              "sku_decl": sorted([r for r in all_sku  if r['diff']<0],key=lambda x:-abs(x['diff']))[:30],
              "sku_gain": sorted([r for r in all_sku  if r['diff']>0],key=lambda x:-abs(x['diff']))[:30],
              "ch_o1":all_ch_o1,
              "ch_decl":sorted([r for r in all_ch if r['diff']<0],key=lambda x:-abs(x['diff']))[:18],
              "ch_gain":sorted([r for r in all_ch if r['diff']>0],key=lambda x:-abs(x['diff']))[:12],
              "hour":sorted(fl(hr_l),key=lambda x:x['key']),
              "anomalies":anoms_d8,
              "city_cho1":fl2(drill['city_cho1']),"city_ch":fl2(drill['city_ch']),
              "city_sku":fl2(drill['city_sku']),
              "city_hour":sorted([flip(r) for r in drill['city_hour']],key=lambda x:(x['k1'],x['k2'])),
              "sku_city":fl2(drill['sku_city']),"sku_ch":fl2(drill['sku_ch']),
              "sku_hour":sorted([flip(r) for r in drill['sku_hour']],key=lambda x:(x['k1'],x['k2'])),
              "city_dev":fl2(drill['city_dev']),"city_disc":fl2(drill['city_disc'])}

    os.makedirs(out_dir, exist_ok=True)
    d2_path = os.path.join(out_dir,'d2.json')
    d8_path = os.path.join(out_dir,'d8.json')
    with open(d2_path,'w') as f: json.dump(d2_out,f,separators=(',',':'))
    with open(d8_path,'w') as f: json.dump(d8_out,f,separators=(',',':'))
    print(f"Written: {d2_path} ({os.path.getsize(d2_path):,} bytes)")
    print(f"Written: {d8_path} ({os.path.getsize(d8_path):,} bytes)")
    return d2_out, d8_out

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    csv_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv)>2 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','public','data')
    run(csv_path, out_dir)
