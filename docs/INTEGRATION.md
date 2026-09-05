# Connecting an app

## 1. Register the app

In the panel, **Add app** with a stable lowercase slug: 2 to 64 characters of letters, digits,
dots and dashes, so a bundle id like `com.acme.myapp` works as well as `my-app`. It is yours to
choose and matches nothing in the stores — the only rule is that the app sends this exact string
in `app`, and that it never changes: redemptions already recorded hang off it. A request from an
unregistered slug is rejected with `unknown_app`.

## 2. Choose a mode

Every redemption carries either a `device_id` or a `nonce`, never both. This is the one decision
that shapes the rest.

### Identified — send `device_id`

Generate a UUID v4 the first time the app runs and keep it in local storage
(`SharedPreferences`, `UserDefaults`, whatever the platform offers). It is not an account and
identifies nobody by name, but it is a stable identifier, so it has to be declared in your store
listing (see the README's privacy section).

What it buys: redeeming the same code again from the same device returns `already` and spends
nothing — a reinstall months later included, as long as the UUID survived. Single-use codes
behave the way people expect.

A reinstall that loses the UUID produces a new one, so a single-use code will not work again.

### Anonymous — send `nonce`

Generate a fresh random string for each redemption attempt and forget it once the call returns.
Nothing that identifies the device ever leaves the app, and the stored redemption is just
"this code was redeemed at this time".

The server remembers the nonce for ten minutes so a retry after a dropped connection returns the
first answer instead of spending a second use. It is held in memory, never written to disk, and
expires on its own.

What it costs: repeat redemptions cannot be recognised. Someone who redeems, reinstalls and
redeems again spends two uses of a code. `max_uses` becomes "how many redemptions" rather than
"how many people".

Pick anonymous when your app declares no data collection and you want to keep it that way. Pick
identified when single-use codes have to be reliable.

## 3. Call the endpoint

```
POST https://redeem.example.com/v1/redeem
Content-Type: application/json

{
  "app": "my-app",
  "code": "FREE99",
  "device_id": "9f1c…",
  "platform": "ios",
  "app_version": "1.4.2",
  "country": "ES"
}
```

`app`, `code` and exactly one of `device_id` / `nonce` are required — sending both, or neither,
is a `bad_request`. The rest is optional and only feeds the panel's stats; anything malformed is
dropped rather than rejected.

| Field | Format |
|---|---|
| `device_id` / `nonce` | up to 128 printable characters, no spaces |
| `platform` | up to 16 chars, `a-z 0-9 _ . -` — e.g. `ios`, `android`, `macos` |
| | required if you restrict codes by platform, see below |
| `app_version` | up to 32 chars, `A-Z a-z 0-9 _ . + -` |
| `country` | ISO 3166-1 alpha-2, e.g. `ES`. Take it from the device region |

Codes are normalized server-side (uppercased, spaces stripped), so send whatever the user typed.

If the server sits behind Cloudflare, the `CF-IPCountry` header wins over the client's `country`:
the device only knows its own locale, the edge knows where the request came from.

The response is always `200` unless the request itself is malformed:

```json
{"granted": true, "reason": "ok"}
```

| `reason` | Meaning | What the app does |
|---|---|---|
| `ok` | Redeemed now | Grant and store |
| `already` | Already redeemed by this device, or a retry of this nonce | Grant and store |
| `unknown` | No such code | Show "invalid code" |
| `wrong_app` | Belongs to another app | Show "invalid code" |
| `wrong_platform` | Restricted to another platform | Show "invalid code" |
| `disabled` | Switched off in the panel | Show "invalid code" |
| `expired` | Past its expiry date | Show "invalid code" |
| `exhausted` | Out of uses | Show "invalid code" |
| `unknown_app` | Slug not registered | Bug: register the app |
| `bad_request` | Missing fields (`400`) | Bug |
| `rate_limited` | Too many attempts (`429`) | Ask the user to retry later |

`granted` is true for both `ok` and `already`. The app only needs to read `granted`; `reason`
distinguishes the error message and helps when debugging.

### Platform-restricted codes

A code can be limited to iOS, to Android, or to both, from the panel. The check runs against the
`platform` the request carries, so a restricted code is rejected with `wrong_platform` when the
app sends nothing to check against. If you use them, send `platform` always.

Unrestricted codes ignore the field and work everywhere, including platforms the panel does not
list.

## 4. Store the grant

When `granted` is true, mark the feature unlocked **locally and permanently**. Do not ask the
server again.

This is deliberate. If the unlock depended on a periodic call, a server outage or a flight
without signal would take it away from someone who has it. The cost is that disabling a code
stops new redemptions but does not revoke old ones.

## 5. Failures

With no network, or the server down, the call fails and the app shows a connection error. There
is no fallback code compiled into the binary: it would be the one code you could never disable.

## Dart example

```dart
Future<bool> redeem(String code) async {
  final response = await http.post(
    Uri.parse('https://redeem.example.com/v1/redeem'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'app': 'my-app',
      'code': code,
      // Identified: a UUID stored on first run.
      'device_id': await deviceId(),
      // Anonymous instead: 'nonce': const Uuid().v4(), generated per attempt.
      'platform': Platform.operatingSystem,
      'app_version': (await PackageInfo.fromPlatform()).version,
      'country': PlatformDispatcher.instance.locale.countryCode,
    }),
  );
  if (response.statusCode != 200) return false;
  return jsonDecode(response.body)['granted'] as bool;
}
```

Retry on a network failure with the **same** nonce, never a new one.

## Notes

- A global code (no app) works in every registered app and spends one use per app it is
  redeemed in.
- Rate limits are 30 requests per minute per IP and 30 per hour per device.
- Send nothing beyond these fields. The request IP is used to rate limit and then forgotten,
  and never stored. See the privacy section of the README for what each mode means for your
  store listing.
