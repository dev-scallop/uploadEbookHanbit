export const config = {
  api: {
    bodyParser: false,
  },
}

import formidable from 'formidable'

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' })

  const form = new formidable.IncomingForm()
  form.parse(req, (err, fields, files) => {
    if (err) {
      console.error(err)
      return res.status(500).json({ error: '파일 파싱 실패' })
    }
    // NOTE: In serverless (Vercel) filesystem is ephemeral. For production, upload to S3/Storage.
    // Here we just return success and file info for demo.
    const file = files.file
    res.status(200).json({ message: '파일 수신(데모): ' + (file?.name || 'unknown'), file: { name: file?.name, size: file?.size } })
  })
}
