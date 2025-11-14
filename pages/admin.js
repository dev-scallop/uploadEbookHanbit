import { useEffect, useState } from 'react'

const STORAGE_KEY = 'pdf-validator-rules'

export default function Admin() {
  const [rules, setRules] = useState(null)
  const [jsonText, setJsonText] = useState('')

  useEffect(() => {
    const local = localStorage.getItem(STORAGE_KEY)
    if (local) {
      try {
        const parsed = JSON.parse(local)
        setRules(parsed)
        setJsonText(JSON.stringify(parsed, null, 2))
        return
      } catch (e) {}
    }
    // fallback to default rules.json
    fetch('/rules.json').then(r => r.json()).then(r => {
      setRules(r)
      setJsonText(JSON.stringify(r, null, 2))
    })
  }, [])

  function save() {
    try {
      const parsed = JSON.parse(jsonText)
      setRules(parsed)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed))
      alert('저장됨 (로컬 저장). 배포 환경에서 영구 저장을 원하면 DB/스토리지 연동 필요)')
    } catch (e) {
      alert('JSON 파싱 오류: ' + e.message)
    }
  }

  function exportJson() {
    const blob = new Blob([jsonText], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'rules.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  function importJson(e) {
    const f = e.target.files?.[0]
    if (!f) return
    f.text().then(t => {
      setJsonText(t)
    })
  }

  return (
    <div style={{ maxWidth: 900, margin: '40px auto', fontFamily: 'system-ui, sans-serif' }}>
      <h1>관리자 — 규격 편집</h1>
      <p>규격을 JSON으로 편집하세요. 저장 시 브라우저 로컬에 보관됩니다. (배포: DB/저장소 연동 권장)</p>

      <div>
        <textarea style={{ width: '100%', height: 360 }} value={jsonText} onChange={e => setJsonText(e.target.value)} />
      </div>
      <div style={{ marginTop: 12 }}>
        <button onClick={save}>저장 (로컬)</button>
        <button style={{ marginLeft: 8 }} onClick={exportJson}>내보내기</button>
        <label style={{ marginLeft: 8 }}>
          가져오기 <input type="file" accept="application/json" style={{ display: 'inline' }} onChange={importJson} />
        </label>
      </div>

      <hr style={{ marginTop: 20 }} />
      <p><a href="/">업로드 페이지로 돌아가기</a></p>
    </div>
  )
}
