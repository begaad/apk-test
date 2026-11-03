package com.example.auditlab;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.graphics.Color;
import android.view.View;
import android.widget.*;
import org.json.*;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private LinearLayout screen;
    private TextView output;
    private String token = "";
    private String base = "http://10.0.2.2:8080";  // Android emulator host. For phone, use PC's LAN IP.

    interface Result { void done(String json); }
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        base = getPreferences(0).getString("base", base);
        showLogin();
    }
    private TextView text(String s, int size) {
        TextView v = new TextView(this); v.setText(s); v.setTextSize(size); v.setTextColor(Color.BLACK); v.setPadding(3, 10, 3, 10); return v;
    }
    private EditText edit(String hint, String value) {
        EditText e = new EditText(this); e.setSingleLine(true); e.setHint(hint); e.setText(value); screen.addView(e); return e;
    }
    private Button button(String title, View.OnClickListener listener) {
        Button b = new Button(this); b.setText(title); b.setOnClickListener(listener); screen.addView(b); return b;
    }
    private void reset(String title) {
        ScrollView scroll = new ScrollView(this);
        screen = new LinearLayout(this); screen.setOrientation(LinearLayout.VERTICAL); screen.setPadding(28, 28, 28, 28);
        scroll.addView(screen); setContentView(scroll); screen.addView(text(title, 24));
    }
    private void resultArea() { output = text("", 14); output.setTextIsSelectable(true); screen.addView(output); }
    private void request(String method, String path, JSONObject body, Result callback) {
        new Thread(() -> {
            String result;
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(base + path).openConnection();
                c.setRequestMethod(method); c.setConnectTimeout(3000); c.setReadTimeout(4000);
                c.setRequestProperty("Accept", "application/json");
                if (!token.isEmpty()) c.setRequestProperty("Authorization", "Bearer " + token);
                if (body != null) {
                    c.setDoOutput(true); c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                    try (OutputStream o = c.getOutputStream()) { o.write(body.toString().getBytes(StandardCharsets.UTF_8)); }
                }
                InputStream stream = c.getResponseCode() < 400 ? c.getInputStream() : c.getErrorStream();
                try (InputStream input = stream; ByteArrayOutputStream buffer = new ByteArrayOutputStream()) {
                    byte[] data = new byte[4096]; int n;
                    while ((n = input.read(data)) != -1) buffer.write(data, 0, n);
                    result = new String(buffer.toByteArray(), StandardCharsets.UTF_8);
                }
                c.disconnect();
            } catch (Exception e) { result = "网络错误：" + e; }
            String response = result;
            handler.post(() -> callback.done(response));
        }).start();
    }
    private void showLogin() {
        reset("轻商店 · Android 客户端");
        screen.addView(text("靶场 API 服务地址（模拟器用 10.0.2.2，真机填电脑局域网 IP）", 14));
        EditText server = edit("服务器地址", base);
        EditText user = edit("用户名", "zhangsan");
        EditText pass = edit("密码", "zhangsan123");
        button("登录", v -> {
            base = server.getText().toString().trim().replaceAll("/+$", "");
            getPreferences(0).edit().putString("base", base).apply();
            try {
                JSONObject body = new JSONObject(); body.put("username", user.getText()); body.put("password", pass.getText());
                request("POST", "/api/v1/auth/login", body, json -> {
                    try {
                        token = new JSONObject(json).getString("token"); showHome();
                    } catch (Exception e) { output.setText(json); }
                });
            } catch (Exception e) { output.setText(e.toString()); }
        });
        resultArea();
    }
    private void showHome() {
        reset("轻商店 · 商品与订单");
        button("查询当前账号", v -> request("GET", "/api/v1/me", null, r -> output.setText(r)));
        button("浏览商品", v -> request("GET", "/api/v1/products", null, r -> output.setText(r)));
        EditText pid = edit("商品 ID，例如 1", "1");
        button("提交订单", v -> {
            try { JSONObject b = new JSONObject(); b.put("product_id", Integer.parseInt(pid.getText().toString()));
                request("POST", "/api/v1/orders", b, r -> output.setText(r));
            } catch (Exception e) { output.setText(e.toString()); }
        });
        button("查看订单", v -> request("GET", "/api/v1/orders", null, r -> output.setText(r)));
        screen.addView(text("账户数据与网络诊断属于客户端辅助功能，适合配合 APK 反编译审计接口。", 14));
        button("账户数据导出", v -> request("GET", "/api/v1/account/export", null, r -> output.setText(r)));
        EditText hostname = edit("诊断域名或 IP", "localhost");
        button("网络诊断", v -> {
            try { JSONObject b = new JSONObject(); b.put("host", hostname.getText().toString());
                request("POST", "/api/v1/tools/diagnose", b, r -> output.setText(r));
            } catch (Exception e) { output.setText(e.toString()); }
        });
        button("退出登录", v -> { token = ""; showLogin(); });
        resultArea();
    }
}
