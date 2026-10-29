# kotsubu-tips-electronics
小粒Tips 電子工作シリーズの配布資料

## ダウンロード履歴

[履歴CSV](data/download-history.csv)に、Release添付ZIPの累計取得回数を記録します。
[Actions](https://github.com/miyama31/kotsubu-tips-electronics/actions/workflows/download-history.yml)の
「Record Release downloads」で実行結果を確認できます。手動実行は「Run workflow」です。

- 毎日07:00（日本時間、cronは前日22:00 UTC）に実行予定です。GitHub側の混雑等で遅延・未実行になる場合があります。
- 日付は予定時刻ではなく実際のAPI取得時の日本時間です。取得日時も日本時間のISO 8601形式（+09:00）です。
- 同じ日・同じタグ・同じZIPは最新の正常取得結果で更新し、重複行を作りません。
- `date_jst`: 取得日、`fetched_at`: 取得日時、`release_tag`: Releaseタグ、`asset_name`: ZIP名、
  `download_count`: 累計取得回数、`increase`: 前回記録日からの増加数です。
- 初回の増加数は空欄です。初回より前や欠測日の履歴は推測しません。欠測があれば増加数は前回正常記録からの差です。
- 数値は人数ではなく取得回数です。この仕組みやテストはZIPをダウンロードしません。
- API失敗、対象不明、累計の減少等ではCSVを更新せず、Actionsを失敗にしてエラーログを残します。
  Actionsの失敗通知設定を確認し、原因解消後に手動で再実行してください。push失敗時もActionsが失敗します。
- 公開リポジトリは60日間活動がないと定期実行が無効になることがあります。Actionsの有効状態も確認してください。

### #03以降の追加

`config/download-targets.json`に`release_tag`と`asset_name`の組を追加してください。
対象ごとに独立した累計と増加数を記録します。認証はActionsの一時的な`GITHUB_TOKEN`を使用し、
書き込み権限は記録ジョブの`contents: write`のみです。CSV保存のためmainへコミットします。
