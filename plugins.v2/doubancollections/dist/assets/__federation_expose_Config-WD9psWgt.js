import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc, c as cloneConfig } from './_plugin-vue_export-helper-Bvtu4dWR.js';

const {createElementVNode:_createElementVNode,resolveComponent:_resolveComponent,createVNode:_createVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,openBlock:_openBlock,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "dc-config pa-4" };
const _hoisted_2 = { class: "d-flex align-center mb-4" };
const _hoisted_3 = { class: "d-flex justify-end mt-6" };

const {onMounted,ref} = await importShared('vue');


const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
},
  emits: ['save', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const localConfig = ref({
  enabled: false,
  show_sidebar_nav: true,
  use_proxy: false,
  collection: 'ECFA5DI7Q',
  cache_hours: 6,
});

// 交给 MoviePilot 宿主保存插件配置。
function saveConfig() {
  emit('save', {
    ...cloneConfig(localConfig.value),
    cache_hours: Math.max(0, Math.min(168, Number(localConfig.value.cache_hours || 0))),
  });
}

onMounted(() => {
  localConfig.value = {
    ...localConfig.value,
    ...cloneConfig(props.initialConfig),
  };
});

return (_ctx, _cache) => {
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VSwitch = _resolveComponent("VSwitch");
  const _component_VTextField = _resolveComponent("VTextField");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _cache[6] || (_cache[6] = _createElementVNode("div", null, [
        _createElementVNode("div", { class: "text-h6" }, "豆瓣合集榜单"),
        _createElementVNode("div", { class: "text-body-2 text-medium-emphasis" }, "使用豆瓣公开榜单数据，不需要 Cookie 或 API Key。")
      ], -1)),
      _createVNode(_component_VSpacer),
      _createVNode(_component_VBtn, {
        icon: "mdi-close",
        variant: "text",
        onClick: _cache[0] || (_cache[0] = $event => (emit('close')))
      })
    ]),
    _createVNode(_component_VAlert, {
      type: "info",
      variant: "tonal",
      density: "compact",
      class: "mb-4"
    }, {
      default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
        _createTextVNode(" 可以填写榜单 ID，也可以直接粘贴 https://m.douban.com/subject_collection/... 地址。 ", -1)
      ]))]),
      _: 1
    }),
    _createVNode(_component_VSwitch, {
      modelValue: localConfig.value.enabled,
      "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((localConfig.value.enabled) = $event)),
      label: "启用插件",
      color: "primary"
    }, null, 8, ["modelValue"]),
    _createVNode(_component_VSwitch, {
      modelValue: localConfig.value.show_sidebar_nav,
      "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((localConfig.value.show_sidebar_nav) = $event)),
      label: "在发现分组显示“豆瓣榜单”",
      color: "primary"
    }, null, 8, ["modelValue"]),
    _createVNode(_component_VSwitch, {
      modelValue: localConfig.value.use_proxy,
      "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((localConfig.value.use_proxy) = $event)),
      label: "访问豆瓣时使用 MoviePilot 代理",
      color: "primary"
    }, null, 8, ["modelValue"]),
    _createVNode(_component_VTextField, {
      modelValue: localConfig.value.collection,
      "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((localConfig.value.collection) = $event)),
      label: "默认豆瓣榜单 ID 或 URL",
      placeholder: "ECFA5DI7Q",
      "prepend-inner-icon": "mdi-link-variant",
      clearable: ""
    }, null, 8, ["modelValue"]),
    _createVNode(_component_VTextField, {
      modelValue: localConfig.value.cache_hours,
      "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((localConfig.value.cache_hours) = $event)),
      modelModifiers: { number: true },
      type: "number",
      min: "0",
      max: "168",
      label: "缓存时长（小时）",
      hint: "填 0 表示每次都请求豆瓣；远端失败时仍会回退到最后一次成功数据。",
      "persistent-hint": ""
    }, null, 8, ["modelValue"]),
    _createElementVNode("div", _hoisted_3, [
      _createVNode(_component_VBtn, {
        color: "primary",
        "prepend-icon": "mdi-content-save",
        onClick: saveConfig
      }, {
        default: _withCtx(() => [...(_cache[8] || (_cache[8] = [
          _createTextVNode("保存", -1)
        ]))]),
        _: 1
      })
    ])
  ]))
}
}

};
const Config = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-bc19b178"]]);

export { Config as default };
