// 兼容 MoviePilot API 包装器和原始 Axios 响应。
export function unwrapResponse(response) {
  if (response && Object.prototype.hasOwnProperty.call(response, 'success')) {
    if (!response.success) throw new Error(response.message || '请求失败')
    return response.data
  }
  const body = response?.data ?? response
  if (body && Object.prototype.hasOwnProperty.call(body, 'success')) {
    if (!body.success) throw new Error(body.message || '请求失败')
    return body.data
  }
  return body
}

// 复制配置，避免直接修改宿主传入的对象。
export function cloneConfig(config) {
  return JSON.parse(JSON.stringify(config || {}))
}
