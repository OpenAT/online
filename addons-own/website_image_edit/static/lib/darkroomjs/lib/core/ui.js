(function() {
'use strict';

Darkroom.UI = {
  Toolbar: Toolbar,
  ButtonGroup: ButtonGroup,
  Button: Button,
};

// Toolbar object.
function Toolbar(element) {
  this.element = element;
}

Toolbar.prototype = {
  createButtonGroup: function(options) {
    var buttonGroup = document.createElement('div');
    buttonGroup.className = 'darkroom-button-group';
    this.element.appendChild(buttonGroup);

    return new ButtonGroup(buttonGroup);
  }
};

// ButtonGroup object.
function ButtonGroup(element) {
  this.element = element;
}

ButtonGroup.prototype = {
  createButton: function(options) {
    var defaults = {
      image: 'help',
      type: 'default',
      group: 'default',
      hide: false,
      disabled: false
    };

    options = Darkroom.Utils.extend(options, defaults);

    var buttonElement = document.createElement('button');
    buttonElement.type = 'button';
    buttonElement.className = 'darkroom-button darkroom-button-' + options.type;

    if (options.image === 'undo') {
      buttonElement.innerHTML = '<i class="fa fa-step-backward"/>';
    } else if (options.image === 'redo') {
      buttonElement.innerHTML = '<i class="fa fa-step-forward"/>';
    } else if (options.image === 'crop') {
      buttonElement.innerHTML = '<i class="fa fa-crop"/>';
    } else if (options.image === 'done') {
      buttonElement.innerHTML = '<i class="fa fa-check"/>';
    } else if (options.image === 'close') {
      buttonElement.innerHTML = '<i class="fa fa-times"/>';
    } else if (options.image === 'rotate-left') {
      buttonElement.innerHTML = '<i class="fa fa-undo"/>';
    } else if (options.image === 'rotate-right') {
      buttonElement.innerHTML = '<i class="fa fa-repeat"/>';
    } else if (options.image === 'mirrorX') {
      buttonElement.innerHTML = '<i class="fa fa-arrows-h"/>';
    } else if (options.image === 'mirrorY') {
      buttonElement.innerHTML = '<i class="fa fa-arrows-v"/>';
    } else if (options.image === 'circle') {
      buttonElement.innerHTML = '<i class="fa fa-circle-o"/>';
    } else if (options.image === 'rounded') {
      buttonElement.innerHTML = '<i class="fa fa-square-o"/>';
    } else if (options.image === 'resize') {
      buttonElement.innerHTML = '<i class="fa fa-arrows-alt"/>';
    }

    this.element.appendChild(buttonElement);

    var button = new Button(buttonElement);
    button.hide(options.hide);
    button.disable(options.disabled);

    return button;
  }
}

// Button object.
function Button(element) {
  this.element = element;
}

Button.prototype = {
  addEventListener: function(eventName, listener) {
    if (this.element.addEventListener){
      this.element.addEventListener(eventName, listener);
    } else if (this.element.attachEvent) {
      this.element.attachEvent('on' + eventName, listener);
    }
  },
  removeEventListener: function(eventName, listener) {
    if (this.element.removeEventListener){
      this.element.removeEventListener(eventName, listener);
    }
  },
  active: function(value) {
    if (value)
      this.element.classList.add('darkroom-button-active');
    else
      this.element.classList.remove('darkroom-button-active');
  },
  hide: function(value) {
    if (value)
      this.element.classList.add('darkroom-button-hidden');
    else
      this.element.classList.remove('darkroom-button-hidden');
  },
  disable: function(value) {
    this.element.disabled = (value) ? true : false;
  }
};

})();
