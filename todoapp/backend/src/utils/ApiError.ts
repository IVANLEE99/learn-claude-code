// 统一错误类

export class ApiError extends Error {
  public readonly statusCode: number
  public readonly code: string

  constructor(statusCode: number, code: string, message: string) {
    super(message)
    this.statusCode = statusCode
    this.code = code
    Object.setPrototypeOf(this, ApiError.prototype)
  }
}
