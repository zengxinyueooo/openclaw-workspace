---
name: ee-conan
description: 云测(conan)设备占用、释放、占用失败参数诊断工具。用于占用Android/iOS/Harmony真机或模拟器，释放已占用的设备，查询在云测的设备占用情况，诊断占用失败原因
---

# 云测设备管理

## 概述

本 skill 提供云测设备（美团云真机平台）的占用、释放、查询、诊断功能。支持的平台包括：
- Android 真机
- iOS 真机
- Harmony 真机
- Android 模拟器（bg、华为云 cph）

**重要规则**：
1. 占用前需要执行 adb devices 检查当前环境是否安装 adb，如果没有安装，先执行 adb 安装，与设备建立 adb 连接时返回 "failed to authenticate"是正常的，返回后再次执行 adb devices 判断设备的真实连接状态(显示"{serialNumebr} device" 为连接正常)
2. 默认使用**短期占用**（occupyTimeoutType = 0），只有用户明确指定需要长期占用时才使用 occupyTimeoutType = 1。
3.  **业务线ID**：使用 `mcp_conan_get_business_lines` 获取真实的 businessLineId，如果用户指定了 businessId，使用用户指定的，如果没有指定，在占用设备前需要帮助用户查询其 businessid
4. **获取 conanKey**，在调用tool前,如果该tool需要参数conanKey，需要使用 `mcp_conan_get_conankey_by_sso` 通过 SSO 信息先获取到 conanKey，用于后续所有接口调用。如果这个工具执行异常或没能获取到正常的 conanKey 值(uuid形式)，显式提示用户到 https://conan.sankuai.com/v2/setup/center 的左侧“持续集成”Tab中点击查询密钥查询
5. 如果用户未指定占用真机还是模拟器，默认占用真机
6. 如果为用户占用设备失败了，主动使用占用失败诊断流程，根据用户是否有指定设备选择对应的工具
7. 占用 bgAndroid14 一定要指定分辨率（1080x2340），因为默认的分辨率配置该规格设备不支持，不传的话占用不到
8. 如果用户真机的占用参数中没有指定useFor字段，但conan_device_diagnose工具返回了设备支持的任务类型不匹配的诊断结果，结果中提到设备不支持component-test类型，此时可能是设备的useFor配置不正确，提示用户向云测团队提[TT工单](https://tt.sankuai.com/public/create?cid=435&tid=4339&iid=39459)解决

## MCP 工具

以下是已支持的的 MCP 工具名称，传递参数时要严格按照工具提供的描述传递

| 功能 | MCP 工具名 |
|------|---------------------|
| SSO获取 mis 与 conanKey | `mcp_conan_get_conankey_by_sso` |
| 占用设备 | `mcp_conan_occupy_device` |
| 释放设备 | `mcp_conan_release_device` |
| 查询占用 | `mcp_conan_query_occupation` |
| 漏斗诊断 | `mcp_conan_funnel_diagnose` |
| 设备诊断 | `mcp_conan_device_diagnose` |
| 获取业务线 | `mcp_conan_get_business_lines` |

## 各平台占用参数示例(极简版)

### 1. Android 真机

```json
{
  "applyCount": 1,
  "deviceFilterModel": {
    "platform": "Android",
    "deviceType": 0,
    "privateKey": "public"
  },
  "businessLineId": <实际业务线ID>,
  "occupyTimeoutType": 0
}
```

### 2. iOS 真机

```json
{
  "applyCount": 1,
  "deviceFilterModel": {
    "platform": "iOS",
    "deviceType": 0,
    "privateKey": "public"
  },
  "businessLineId": <实际业务线ID>,
  "occupyTimeoutType": 0
}
```

### 3. Harmony 真机

```json
{
  "applyCount": 1,
  "deviceFilterModel": {
    "platform": "Harmony",
    "deviceType": 0,
    "privateKey": "public"
  },
  "businessLineId": <实际业务线ID>,
  "occupyTimeoutType": 0
}
```

### 4. bg Android9 模拟器（分辨率为 1080x1920）

```json
{
  "applyCount": 1,
  "deviceFilterModel": {
    "platform": "Android",
    "deviceType": 1,
    "privateKey": "public",
    "vendor": "bg"
  },
  "businessLineId": <实际业务线ID>,
  "occupyTimeoutType": 0
}
```

### 5. bg Android14 模拟器（分辨率 1080x2340）

**注意**：bg Android14 一定要指定分辨率，因为默认分辨率没有该版本设备。

```json
{
  "applyCount": 1,
  "deviceFilterModel": {
    "platform": "Android",
    "deviceType": 1,
    "versions": ["14"],
    "vendor": "bg",
    "width": 1080,
    "height": 2340
  },
  "businessLineId": <实际业务线ID>,
  "occupyTimeoutType": 0
}
```

### 6. 华为云 cph Android9 模拟器（分辨率为 1080x1920）

**注意**：华为云 cph 目前仅支持 Android9。

```json
{
  "applyCount": 1,
  "deviceFilterModel": {
    "platform": "Android",
    "deviceType": 1,
    "vendor": "cph"
  },
  "businessLineId": <实际业务线ID>,
  "occupyTimeoutType": 0
}
```


## 使用流程

### 完整占用流程

**第一步：获取 mis 与 conanKey（必需）**

```
调用 mcp_conan_get_conankey_by_sso 通过 SSO 获取用户 mis 与认证凭证
```

**第二步：获取业务线ID**（如用户未传入）:

```
调用 mcp_conan_get_business_lines 获取用户可用的业务线列表
```

**第三步：构造占用请求**:

```
根据上面的示例选择对应平台的JSON模板
填写实际的 businessLineId
确保 occupyTimeoutType = 0（短期占用）
```

**第四步：执行占用**:

```
调用 mcp_conan_occupy_device
```

**第五步：处理占用结果**:

- 成功：获取 serialNumber 和 remoteConnectAddress
- 失败：使用诊断接口排查原因
  - **如果是设备占用达到上限**（每个人最多同时占用5台）：
    1. 调用 `mcp_conan_query_occupation` 查询当前已占用的设备列表
    2. 展示已占用设备信息（包含 serialNumber 和 remoteConnectAddress）
    3. 询问用户选择：
       - 是否需要释放其中一台或多台设备 → 调用 `mcp_conan_release_device` 释放指定设备
       - 是否继续使用已占用的设备 → 提供已占用设备的连接信息

**第六步：使用完毕释放设备**:

```
调用 mcp_conan_release_device，传入占用的设备序列号
```

### 诊断流程

当占用失败时：

1. **漏斗分析**：如果用户没有指定需要占用的设备，使用mcp_conan_funnel_diagnose定位在哪一步设备数量不足，参数要严格按照工具的描述传递
3. **指定设备诊断**：如果用户指定了需要占用的设备列表，使用mcp_conan_device_diagnose排查占不到这些设备的原因，参数要严格按照工具的描述传递
