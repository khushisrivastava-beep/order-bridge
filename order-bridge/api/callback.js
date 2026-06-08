export default async function handler(req, res) {
  const { code, error } = req.query;

  if (error || !code) {
    return res.redirect('/?error=access_denied');
  }

  const clientId     = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri  = process.env.REDIRECT_URI;
  const secret       = process.env.SESSION_SECRET;

  try {
    // Exchange code for tokens
    const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        code,
        client_id:     clientId,
        client_secret: clientSecret,
        redirect_uri:  redirectUri,
        grant_type:    'authorization_code',
      }),
    });

    const tokens = await tokenRes.json();
    if (!tokens.id_token) throw new Error('No id_token returned');

    // Decode the JWT payload (no verification needed — Google already validated it)
    const payload = JSON.parse(
      Buffer.from(tokens.id_token.split('.')[1], 'base64url').toString()
    );

    const email = payload.email || '';
    const domain = email.split('@')[1] || '';

    if (domain !== '1mg.com') {
      return res.redirect('/?error=unauthorized');
    }

    // Set a signed session cookie (email + expiry + simple HMAC)
    const expires = Date.now() + 8 * 60 * 60 * 1000; // 8 hours
    const data    = `${email}|${expires}`;
    // Simple HMAC-like signature using secret
    const crypto  = await import('crypto');
    const sig = crypto.createHmac('sha256', secret).update(data).digest('hex');
    const cookieVal = Buffer.from(JSON.stringify({ data, sig })).toString('base64');

    res.setHeader('Set-Cookie',
      `ob_session=${cookieVal}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=28800`
    );
    res.redirect('/');

  } catch (err) {
    console.error('OAuth error:', err);
    res.redirect('/?error=oauth_error');
  }
}
