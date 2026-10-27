"""Local, self-contained HTML report: embedded figures and scenario navigation."""

import base64
import html
import json


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gait State Estimation Lab</title><link rel="icon" href="data:,">
<style>
:root{--ink:#163047;--muted:#52677a;--blue:#176c9c;--line:#dce6ec;--paper:#fff;--bg:#f2f6f8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}
main{max-width:1250px;margin:auto;padding:36px 24px 60px}header{border-bottom:1px solid var(--line);padding-bottom:24px}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.14em;color:var(--blue);text-transform:uppercase}
h1{font-size:clamp(30px,5vw,48px);line-height:1.12;margin:12px 0}h2{margin:0 0 8px;font-size:23px}p{color:var(--muted);max-width:850px;margin:10px 0}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}.pill{padding:4px 10px;border:1px solid var(--line);border-radius:20px;font-size:12px;background:white}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0}button{font:inherit;font-size:14px;border:1px solid var(--line);border-radius:7px;padding:10px 14px;background:white;color:var(--ink);cursor:pointer}
button[aria-pressed="true"]{background:var(--ink);color:white;border-color:var(--ink)}button:focus-visible{outline:3px solid #e8b15d;outline-offset:2px}
.panel{padding:24px;background:var(--paper);border:1px solid var(--line);border-radius:12px;margin-bottom:20px}.figure{width:100%;height:auto;display:block;border-top:1px solid var(--line);margin-top:20px}
table{border-collapse:collapse;width:100%;font-size:14px;margin-top:20px}th,td{text-align:left;padding:11px 12px;border-bottom:1px solid var(--line)}th{font-size:12px;color:var(--muted)}.table-scroll{overflow:auto}
a{color:var(--blue)}.footnote{font-size:13px}.details{display:flex;gap:20px;flex-wrap:wrap;margin-top:18px}.metric{flex:1;min-width:160px;padding:15px;background:var(--bg);border-radius:8px}.metric b{font-size:23px;display:block}.metric span{color:var(--muted);font-size:12px}footer{font-size:13px;color:var(--muted);padding-top:8px}
</style></head><body><main>
<header><div class="eyebrow">Signal processing / system identification / state estimation</div>
<h1>Gait State Estimation Lab</h1>
<p>Inspect a four-state Extended Kalman Filter on synthetic IMU observations. Compare spectral and Hilbert estimates, track known phase, and test missing observations and model mismatch.</p>
<div class="pills"><span class="pill">Independent calibration record</span><span class="pill">Fixed random seed: __SEED__</span><span class="pill">25 Hz</span><span class="pill">Offline benchmark</span></div></header>
<nav aria-label="Simulation scenarios">__BUTTONS__</nav>
<section class="panel" aria-live="polite"><h2 id="case-title"></h2><p id="case-description"></p>
<div class="details"><div class="metric"><b id="frequency"></b><span>Signal-selected fundamental</span></div><div class="metric"><b id="phase-error"></b><span>EKF relative phase MAE</span></div><div class="metric"><b id="gap"></b><span>EKF coverage inside observation gap</span></div></div>
<img class="figure" id="figure" alt="Six-panel signal processing and state estimation comparison">
<div class="table-scroll"><table><thead><tr><th>Estimator</th><th>Relative phase MAE</th><th>Right phase MAE</th><th>Gap prediction coverage</th><th>Phase MAE inside gap</th></tr></thead><tbody id="metrics"></tbody></table></div>
<p class="footnote">Errors use identical observed support after initialization and filter-edge exclusion. Gap prediction is evaluated separately. The dominant-band comparator tracks an oscillation that may be a harmonic, so its phase is a different cycle variable.</p>
<div class="details"><a id="download-image">Download figure</a><a id="download-data">Inspect time series (CSV)</a><a href="summary.json">Benchmark summary</a><a href="manifest.json">Run manifest</a></div>
</section>
<footer>All observations and references in this report are synthetic. Local covariance bands are EKF approximations, not calibrated confidence guarantees. The model is deliberately challenged by waveform changes; a complex estimator is not assumed to outperform its baseline.</footer>
</main><script id="demo-data" type="application/json">__PAYLOAD__</script><script>
const cases=JSON.parse(document.getElementById('demo-data').textContent);
const names={dominant_hilbert:'Hilbert · dominant band',fundamental_hilbert:'Hilbert · fundamental',harmonic_ekf:'Harmonic EKF'};
const metric=(x,unit)=>x===null?'Not applicable':x.toFixed(2)+unit;
function selectCase(index){const c=cases[index],m=c.metrics.harmonic_ekf;
document.getElementById('case-title').textContent=c.title;document.getElementById('case-description').textContent=c.description;
document.getElementById('frequency').textContent=c.frequency_selection.right.fundamental_hz.toFixed(3)+' Hz';
document.getElementById('phase-error').textContent=m.relative_phase_mae_deg.toFixed(2)+'°';
document.getElementById('gap').textContent=m.gap_prediction_coverage===null?'No gap':(100*m.gap_prediction_coverage).toFixed(0)+'%';
document.getElementById('figure').src=c.image;
const body=document.getElementById('metrics');body.replaceChildren();
Object.entries(c.metrics).forEach(([name,v])=>{const row=document.createElement('tr');[names[name],metric(v.relative_phase_mae_deg,'°'),metric(v.right_phase_mae_deg,'°'),v.gap_prediction_coverage===null?'Not applicable':(100*v.gap_prediction_coverage).toFixed(0)+'%',metric(v.gap_phase_mae_deg,'°')].forEach(value=>{const cell=document.createElement('td');cell.textContent=value;row.appendChild(cell)});body.appendChild(row)});
const figure=document.getElementById('download-image');figure.href=c.scenario+'.png';figure.download=c.scenario+'.png';
const data=document.getElementById('download-data');data.href=c.scenario+'_timeseries.csv';data.download=c.scenario+'_timeseries.csv';
document.querySelectorAll('nav button').forEach((button,i)=>button.setAttribute('aria-pressed',String(i===index)))}
document.querySelectorAll('nav button').forEach((button,i)=>button.addEventListener('click',()=>selectCase(i)));selectCase(0);
</script></body></html>"""


def write_report(result, output_dir):
    cases = []
    for case in result["cases"]:
        picture = base64.b64encode(
            (output_dir / f"{case['scenario']}.png").read_bytes()
        ).decode("ascii")
        cases.append({**case, "image": f"data:image/png;base64,{picture}"})
    buttons = "".join(
        f'<button type="button" aria-pressed="false">{html.escape(case["title"])}</button>'
        for case in cases
    )
    payload = json.dumps(cases, allow_nan=False).replace("</", "<\\/")
    page = (
        TEMPLATE.replace("__SEED__", str(result["parameters"]["seed"]))
        .replace("__BUTTONS__", buttons)
        .replace("__PAYLOAD__", payload)
    )
    (output_dir / "report.html").write_text(page, encoding="utf-8")
