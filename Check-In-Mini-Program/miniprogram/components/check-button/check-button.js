// components/check-button/check-button.js
Component({
  properties: {
    checked: {
      type: Boolean,
      value: false
    }
  },

  data: {
    animating: false
  },

  methods: {
    onTap() {
      if (this.properties.checked) {
        return
      }

      this.setData({ animating: true })
      setTimeout(() => {
        this.setData({ animating: false })
      }, 300)

      this.triggerEvent('tap')
    }
  }
})
