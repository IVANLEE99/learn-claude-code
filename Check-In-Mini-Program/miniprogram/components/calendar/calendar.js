// components/calendar/calendar.js
Component({
  properties: {
    year: {
      type: Number,
      value: new Date().getFullYear()
    },
    month: {
      type: Number,
      value: new Date().getMonth() + 1
    },
    checkinDates: {
      type: Array,
      value: []
    }
  },

  data: {
    weekdays: ['日', '一', '二', '三', '四', '五', '六'],
    emptyDays: [],
    days: []
  },

  observers: {
    'year, month, checkinDates': function(year, month, checkinDates) {
      this.generateCalendar(year, month, checkinDates)
    }
  },

  lifetimes: {
    attached() {
      const { year, month, checkinDates } = this.properties
      this.generateCalendar(year, month, checkinDates)
    }
  },

  methods: {
    generateCalendar(year, month, checkinDates) {
      const checkinSet = new Set(checkinDates)
      const firstDay = new Date(year, month - 1, 1).getDay()
      const daysInMonth = new Date(year, month, 0).getDate()
      const today = new Date()
      const todayStr = this.formatDate(today)

      const emptyDays = Array(firstDay).fill(null)
      const days = []

      for (let i = 1; i <= daysInMonth; i++) {
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(i).padStart(2, '0')}`
        const date = new Date(year, month - 1, i)
        const isFuture = date > today && dateStr !== todayStr

        days.push({
          day: i,
          date: dateStr,
          isToday: dateStr === todayStr,
          isCheckedIn: checkinSet.has(dateStr),
          isFuture
        })
      }

      this.setData({ emptyDays, days })
    },

    formatDate(date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
  }
})
