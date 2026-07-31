import { importShared } from './__federation_fn_import-JrT3xvdd.js';
import { _ as _export_sfc, u as unwrapResponse } from './_plugin-vue_export-helper-Bvtu4dWR.js';

const {createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,resolveComponent:_resolveComponent,createVNode:_createVNode,normalizeStyle:_normalizeStyle,createTextVNode:_createTextVNode,withCtx:_withCtx,createBlock:_createBlock,renderList:_renderList,Fragment:_Fragment,normalizeClass:_normalizeClass} = await importShared('vue');


const _hoisted_1 = { class: "dc-page" };
const _hoisted_2 = { class: "dc-hero__content" };
const _hoisted_3 = {
  key: 0,
  class: "dc-title"
};
const _hoisted_4 = {
  key: 1,
  class: "dc-title dc-title--compact"
};
const _hoisted_5 = { class: "dc-meta" };
const _hoisted_6 = { key: 0 };
const _hoisted_7 = { key: 1 };
const _hoisted_8 = { key: 2 };
const _hoisted_9 = { class: "dc-hero__actions" };
const _hoisted_10 = { class: "dc-layout" };
const _hoisted_11 = {
  class: "dc-regions",
  "aria-label": "地区筛选"
};
const _hoisted_12 = ["onClick"];
const _hoisted_13 = { class: "dc-main" };
const _hoisted_14 = {
  class: "dc-filters",
  "aria-label": "类型筛选"
};
const _hoisted_15 = ["onClick"];
const _hoisted_16 = {
  key: 0,
  class: "dc-grid"
};
const _hoisted_17 = {
  key: 1,
  class: "dc-grid"
};
const _hoisted_18 = ["aria-label", "onClick"];
const _hoisted_19 = ["src", "alt"];
const _hoisted_20 = {
  key: 1,
  class: "dc-poster dc-poster--empty"
};
const _hoisted_21 = { class: "dc-rank" };
const _hoisted_22 = {
  key: 2,
  class: "dc-rating"
};
const _hoisted_23 = { class: "dc-card__body" };
const _hoisted_24 = ["onClick"];
const _hoisted_25 = { class: "dc-card__subtitle" };
const _hoisted_26 = { class: "dc-card__footer" };
const _hoisted_27 = {
  key: 0,
  class: "dc-votes"
};
const _hoisted_28 = { key: 1 };
const _hoisted_29 = {
  key: 2,
  class: "dc-empty"
};
const _hoisted_30 = {
  key: 3,
  class: "dc-load-more"
};

const {computed,inject,onMounted,ref} = await importShared('vue');


const _sfc_main = {
  __name: 'AppPage',
  props: {
  api: {
    type: Object,
    default: () => ({}),
  },
  nativeSubscribe: {
    type: Function,
    default: null,
  },
  pluginId: {
    type: String,
    default: 'DoubanCollections',
  },
  hideTitle: {
    type: Boolean,
    default: false,
  },
},
  setup(__props, { expose: __expose }) {

const props = __props;

const hostToast = inject('moviepilot:toast', null);
const injectedSubscribe = inject('moviepilot:nativeSubscribe', null);
const loading = ref(false);
const loadingMore = ref(false);
const error = ref('');
const payload = ref({
  collection: {},
  categories: [],
  items: [],
  source: '',
  stale: false,
});

const pluginBase = computed(() => `plugin/${props.pluginId || 'DoubanCollections'}`);
const collection = computed(() => payload.value.collection || {});
const categories = computed(() => payload.value.categories || []);
const items = computed(() => payload.value.items || []);
const currentId = computed(() => collection.value.id || '');
const hasMore = computed(() => items.value.length < Number(collection.value.total || 0));
const activeCategory = computed(() => {
  return categories.value.find(category => category.items.some(item => item.current || item.id === currentId.value))
    || categories.value[0]
    || { name: '', items: [] }
});
const filters = computed(() => activeCategory.value.items || []);
const heroStyle = computed(() => {
  if (!collection.value.backdrop) return {}
  return { backgroundImage: `linear-gradient(90deg, rgba(18,18,24,.92), rgba(18,18,24,.54)), url("${collection.value.backdrop}")` }
});

// 读取指定榜单；翻页时只追加条目，不替换筛选矩阵。
async function loadCollection(collectionId = '', start = 0, refresh = false, append = false) {
  if (append) loadingMore.value = true;
  else loading.value = true;
  error.value = '';
  try {
    const params = new URLSearchParams({
      collection_id: collectionId,
      start: String(start),
      count: '20',
      refresh: String(refresh),
    });
    const response = await props.api.get(`${pluginBase.value}/collection?${params.toString()}`);
    const data = unwrapResponse(response);
    if (append) {
      const known = new Set(items.value.map(item => item.id));
      payload.value = {
        ...payload.value,
        ...data,
        items: [...items.value, ...(data.items || []).filter(item => !known.has(item.id))],
      };
    } else {
      payload.value = data || payload.value;
    }
  } catch (err) {
    error.value = err?.message || '榜单加载失败';
    hostToast?.error?.(error.value);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

// 切换左侧地区时，优先保持当前类型；不存在时选择该地区首个真实榜单。
function selectCategory(category) {
  const preferred = category.items.find(item => item.name === collection.value.filter_name)
    || category.items[0];
  if (preferred) loadCollection(preferred.id);
}

// 切换当前地区下的类型榜单。
function selectFilter(filter) {
  if (filter.id !== currentId.value) loadCollection(filter.id);
}

// 调用 MoviePilot 原生订阅；旧宿主没有该能力时打开豆瓣详情。
async function subscribe(item) {
  const subscribeHandler = props.nativeSubscribe || injectedSubscribe;
  if (!subscribeHandler) {
    openDouban(item.url);
    hostToast?.info?.('当前 MoviePilot 版本不支持插件原生订阅，已打开豆瓣详情');
    return
  }
  const result = await subscribeHandler({
    title: item.title,
    type: item.type === 'movie' ? '电影' : '电视剧',
    year: item.year,
    douban_id: item.id,
    media_id: item.id,
    mediaid_prefix: 'douban',
  });
  if (result && !result.success && result.code === 'INVALID_MEDIA') openDouban(item.url);
}

// 在新标签页打开可信的豆瓣链接。
function openDouban(url) {
  if (/^https:\/\/(?:movie|m)\.douban\.com\//.test(url || '')) {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
}

// 将关注人数格式化为紧凑中文。
function formatFollowers(value) {
  const number = Number(value || 0);
  if (number >= 10000) return `${(number / 10000).toFixed(number >= 100000 ? 0 : 1)} 万人关注`
  return number > 0 ? `${number.toLocaleString()} 人关注` : ''
}

// 将评分人数格式化为紧凑数字。
function formatCount(value) {
  const number = Number(value || 0);
  if (number >= 10000) return `${(number / 10000).toFixed(1)}万`
  return number.toLocaleString()
}

__expose({ loadCollection, loading });
onMounted(() => loadCollection());

return (_ctx, _cache) => {
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VSkeletonLoader = _resolveComponent("VSkeletonLoader");
  const _component_VIcon = _resolveComponent("VIcon");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("section", {
      class: "dc-hero",
      style: _normalizeStyle(heroStyle.value)
    }, [
      _createElementVNode("div", _hoisted_2, [
        _cache[3] || (_cache[3] = _createElementVNode("div", { class: "dc-eyebrow" }, "DOUBAN COLLECTION", -1)),
        (!__props.hideTitle)
          ? (_openBlock(), _createElementBlock("h1", _hoisted_3, _toDisplayString(collection.value.name || '豆瓣榜单'), 1))
          : (_openBlock(), _createElementBlock("h2", _hoisted_4, _toDisplayString(collection.value.name || '豆瓣榜单'), 1)),
        _createElementVNode("div", _hoisted_5, [
          (formatFollowers(collection.value.followers))
            ? (_openBlock(), _createElementBlock("span", _hoisted_6, _toDisplayString(formatFollowers(collection.value.followers)), 1))
            : _createCommentVNode("", true),
          _createElementVNode("span", null, _toDisplayString(collection.value.total || 0) + " 个条目", 1),
          (collection.value.updated_at)
            ? (_openBlock(), _createElementBlock("span", _hoisted_7, "更新于 " + _toDisplayString(collection.value.updated_at), 1))
            : _createCommentVNode("", true),
          (payload.value.source === 'cache')
            ? (_openBlock(), _createElementBlock("span", _hoisted_8, "缓存数据"))
            : _createCommentVNode("", true)
        ])
      ]),
      _createElementVNode("div", _hoisted_9, [
        _createVNode(_component_VBtn, {
          icon: "mdi-refresh",
          variant: "tonal",
          loading: loading.value,
          title: "刷新",
          onClick: _cache[0] || (_cache[0] = $event => (loadCollection(currentId.value, 0, true)))
        }, null, 8, ["loading"]),
        _createVNode(_component_VBtn, {
          icon: "mdi-open-in-new",
          variant: "tonal",
          title: "打开豆瓣原榜单",
          onClick: _cache[1] || (_cache[1] = $event => (openDouban(collection.value.url)))
        })
      ])
    ], 4),
    (payload.value.stale)
      ? (_openBlock(), _createBlock(_component_VAlert, {
          key: 0,
          type: "warning",
          variant: "tonal",
          density: "compact",
          class: "ma-4 mb-0"
        }, {
          default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
            _createTextVNode(" 豆瓣暂时无法访问，当前显示最后一次成功缓存。 ", -1)
          ]))]),
          _: 1
        }))
      : _createCommentVNode("", true),
    (error.value)
      ? (_openBlock(), _createBlock(_component_VAlert, {
          key: 1,
          type: "error",
          variant: "tonal",
          density: "compact",
          class: "ma-4 mb-0"
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(error.value), 1)
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    _createElementVNode("div", _hoisted_10, [
      _createElementVNode("aside", _hoisted_11, [
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(categories.value, (category) => {
          return (_openBlock(), _createElementBlock("button", {
            key: category.name,
            class: _normalizeClass(["dc-region", { 'dc-region--active': category.name === activeCategory.value.name }]),
            type: "button",
            onClick: $event => (selectCategory(category))
          }, _toDisplayString(category.name), 11, _hoisted_12))
        }), 128))
      ]),
      _createElementVNode("main", _hoisted_13, [
        _createElementVNode("div", _hoisted_14, [
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(filters.value, (filter) => {
            return (_openBlock(), _createElementBlock("button", {
              key: filter.id,
              class: _normalizeClass(["dc-filter", { 'dc-filter--active': filter.id === currentId.value }]),
              type: "button",
              onClick: $event => (selectFilter(filter))
            }, _toDisplayString(filter.name), 11, _hoisted_15))
          }), 128))
        ]),
        (loading.value && !items.value.length)
          ? (_openBlock(), _createElementBlock("div", _hoisted_16, [
              (_openBlock(), _createElementBlock(_Fragment, null, _renderList(10, (index) => {
                return _createVNode(_component_VSkeletonLoader, {
                  key: index,
                  type: "image, article",
                  class: "dc-skeleton"
                })
              }), 64))
            ]))
          : (items.value.length)
            ? (_openBlock(), _createElementBlock("div", _hoisted_17, [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(items.value, (item) => {
                  return (_openBlock(), _createElementBlock("article", {
                    key: item.id,
                    class: "dc-card"
                  }, [
                    _createElementVNode("button", {
                      class: "dc-poster-wrap",
                      type: "button",
                      "aria-label": `打开 ${item.title} 的豆瓣详情`,
                      onClick: $event => (openDouban(item.url))
                    }, [
                      (item.poster)
                        ? (_openBlock(), _createElementBlock("img", {
                            key: 0,
                            class: "dc-poster",
                            src: item.poster,
                            alt: `${item.title} 海报`,
                            loading: "lazy",
                            referrerpolicy: "no-referrer"
                          }, null, 8, _hoisted_19))
                        : (_openBlock(), _createElementBlock("div", _hoisted_20, "暂无海报")),
                      _createElementVNode("span", _hoisted_21, _toDisplayString(item.rank), 1),
                      (item.rating)
                        ? (_openBlock(), _createElementBlock("span", _hoisted_22, _toDisplayString(item.rating), 1))
                        : _createCommentVNode("", true)
                    ], 8, _hoisted_18),
                    _createElementVNode("div", _hoisted_23, [
                      _createElementVNode("button", {
                        class: "dc-card__title",
                        type: "button",
                        onClick: $event => (openDouban(item.url))
                      }, _toDisplayString(item.title), 9, _hoisted_24),
                      _createElementVNode("div", _hoisted_25, _toDisplayString(item.subtitle || item.year || '暂无简介'), 1),
                      _createElementVNode("div", _hoisted_26, [
                        (item.rating_count)
                          ? (_openBlock(), _createElementBlock("span", _hoisted_27, _toDisplayString(formatCount(item.rating_count)) + " 人评分", 1))
                          : (_openBlock(), _createElementBlock("span", _hoisted_28)),
                        _createVNode(_component_VBtn, {
                          size: "small",
                          variant: "tonal",
                          color: "primary",
                          "prepend-icon": "mdi-plus",
                          onClick: $event => (subscribe(item))
                        }, {
                          default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                            _createTextVNode(" 订阅 ", -1)
                          ]))]),
                          _: 1
                        }, 8, ["onClick"])
                      ])
                    ])
                  ]))
                }), 128))
              ]))
            : (!loading.value)
              ? (_openBlock(), _createElementBlock("div", _hoisted_29, [
                  _createVNode(_component_VIcon, {
                    icon: "mdi-movie-open-off-outline",
                    size: "52"
                  }),
                  _cache[6] || (_cache[6] = _createElementVNode("div", null, "这个榜单暂时没有条目", -1))
                ]))
              : _createCommentVNode("", true),
        (hasMore.value)
          ? (_openBlock(), _createElementBlock("div", _hoisted_30, [
              _createVNode(_component_VBtn, {
                variant: "tonal",
                loading: loadingMore.value,
                onClick: _cache[2] || (_cache[2] = $event => (loadCollection(currentId.value, items.value.length, false, true)))
              }, {
                default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
                  _createTextVNode(" 加载更多 ", -1)
                ]))]),
                _: 1
              }, 8, ["loading"])
            ]))
          : _createCommentVNode("", true)
      ])
    ])
  ]))
}
}

};
const AppPage = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-4a4f1ac3"]]);

export { AppPage as default };
