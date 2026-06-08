export default async function handler(req, res) {
  const secret  = process.env.SESSION_SECRET;
  const cookies = req.headers.cookie || '';
  const match   = cookies.match(/ob_session=([^;]+)/);

  if (!match) {
    return res.status(401).json({ ok: false });
  }

  try {
    const parsed   = JSON.parse(Buffer.from(match[1], 'base64').toString());
    const { data, sig } = parsed;
    const crypto   = await import('crypto');
    const expected = crypto.createHmac('sha256', secret).update(data).digest('hex');

    if (sig !== expected) return res.status(401).json({ ok: false });

    const [email, expiresStr] = data.split('|');
    if (Date.now() > parseInt(expiresStr)) return res.status(401).json({ ok: false });

    return res.status(200).json({ ok: true, email });
  } catch {
    return res.status(401).json({ ok: false });
  }
}
