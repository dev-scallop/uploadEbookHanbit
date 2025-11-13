import { useEffect, useState } from 'react'
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf.js'

export default function Home() {
  const [file, setFile] = useState(null)
  const [rules, setRules] = useState(null)
  const [errors, setErrors] = useState([])
  const [report, setReport] = useState(null)

  useEffect(() => {
    // load default rules from public/rules.json
    fetch('/rules.json').then(r => r.json()).then(r => setRules(r))
  }, [])

  async function validatePdf(file) {
    setErrors([])
    setReport(null)
    if (!file) return
    const errs = []

    // file size check
    const maxMB = rules?.maxFileSizeMB ?? 20
    if (file.size / 1024 / 1024 > maxMB) {
      errs.push({ type: 'size', message: `파일 크기 초과: ${Math.round(file.size/1024/1024*100)/100}MB > ${maxMB}MB` })
    }

    const arrayBuffer = await file.arrayBuffer()

    try {
      const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
      const pdf = await loadingTask.promise

      // encryption check
      if (rules?.disallowEncrypted && pdf.numPages === 0) {
        errs.push({ type: 'encrypted', message: '암호화된 PDF 또는 권한 제한됨' })
      }

      // page count
      const numPages = pdf.numPages
      if (rules?.minPages && numPages < rules.minPages) {
        errs.push({ type: 'pages', message: `페이지 수가 너무 적음: ${numPages} < ${rules.minPages}` })
      }
      if (rules?.maxPages && numPages > rules.maxPages) {
        errs.push({ type: 'pages', message: `페이지 수가 너무 많음: ${numPages} > ${rules.maxPages}` })
      }

      // check first page size (assume uniform)
      const page = await pdf.getPage(1)
      const viewport = page.getViewport({ scale: 1 })
      // PDF points: 1 pt = 1/72 inch. Convert to mm: 1 inch = 25.4 mm
      const widthPt = viewport.width
      const heightPt = viewport.height
      const widthMm = (widthPt / 72) * 25.4
      const heightMm = (heightPt / 72) * 25.4

      if (rules?.pageSize) {
        const { widthMm: wantW, heightMm: wantH, toleranceMm = 5 } = rules.pageSize
        const deltaW = Math.abs(widthMm - wantW)
        const deltaH = Math.abs(heightMm - wantH)
        if (deltaW > toleranceMm || deltaH > toleranceMm) {
          errs.push({ type: 'pagesize', message: `페이지 사이즈 불일치: ${Math.round(widthMm)}x${Math.round(heightMm)}mm (허용오차 ${toleranceMm}mm). 기대: ${wantW}x${wantH}mm` })
        }
      }

      // metadata check
      if (rules?.requireMetadata && rules.requireMetadata.length > 0) {
        try {
          const md = await pdf.getMetadata()
          const info = md.info || {}
          for (const key of rules.requireMetadata) {
            // PDF.js returns keys like Title, Author
            if (!info[key]) {
              errs.push({ type: 'metadata', message: `메타데이터 누락: ${key}` })
            }
          }
        } catch (e) {
          errs.push({ type: 'metadata', message: '메타데이터를 읽는 중 오류 발생' })
        }
      }

      setReport({ numPages, widthMm: Math.round(widthMm), heightMm: Math.round(heightMm) })
    } catch (e) {
      errs.push({ type: 'parse', message: 'PDF 파싱 실패: 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.' })
    }

    setErrors(errs)
    return errs
  }

  async function onSubmit(e) {
    e.preventDefault()
    if (!file) return
    const errs = await validatePdf(file)
    if (errs.length === 0) {
      // POST to /api/upload (stub)
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      const json = await res.json()
      alert('업로드 성공: ' + (json.message || 'OK'))
    } else {
      // show errors and prompt reupload
      // we already set errors state
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '40px auto', fontFamily: 'system-ui, sans-serif' }}>
      <h1>전자책 PDF 업로드</h1>
      <p>업로드하기 전에 PDF가 규격에 맞는지 검사합니다. 규격은 관리자 페이지에서 수정하세요.</p>

      <form onSubmit={onSubmit}>
        <div>
          <input type="file" accept="application/pdf" onChange={e => setFile(e.target.files?.[0] ?? null)} />
        </div>
        <div style={{ marginTop: 12 }}>
          <button type="submit">검증 후 업로드</button>
        </div>
      </form>

      {report && (
        <div style={{ marginTop: 20 }}>
          <h3>검사 결과</h3>
          <div>페이지 수: {report.numPages}</div>
          <div>페이지 크기(첫 페이지): {report.widthMm} x {report.heightMm} mm</div>
        </div>
      )}

      {errors && errors.length > 0 && (
        <div style={{ marginTop: 20, border: '1px solid #e33', padding: 12, background: '#fff6f6' }}>
          <h3>오류 — 업로드할 수 없습니다</h3>
          <ul>
            {errors.map((er, i) => (
              <li key={i}><strong>{er.type}</strong>: {er.message}</li>
            ))}
          </ul>
          <p>지적된 항목을 수정한 뒤 다시 업로드 해주세요.</p>
        </div>
      )}

      <hr style={{ marginTop: 30 }} />
      <p><a href="/admin">관리자(규격 편집)</a></p>
    </div>
  )
}
