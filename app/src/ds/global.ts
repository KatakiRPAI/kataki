// The design system's bundle reads React from the window when it loads, so this runs first.
import * as React from 'react'
;(window as unknown as { React: typeof React }).React = React
